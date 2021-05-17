from typing import TypedDict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool
from app.celery import celery as celery_app
from app.core import tasks
from app import schemas
from celery import Celery

from uuid import UUID
import uuid
import threading
import asyncio
import collections

router = APIRouter()


class CeleryEventsListener:
    def __init__(self, app: Celery) -> None:
        self._state = app.events.State()
        self._connections: dict[
            UUID, dict[UUID, tuple[WebSocket, asyncio.AbstractEventLoop]]
        ] = collections.defaultdict(lambda: {})
        self._connections_id: dict[UUID, UUID] = {}

        with app.connection() as connection:
            self._receiver = app.events.Receiver(
                connection,
                handlers={
                    "*": self.callback,
                },
            )

    def start(self) -> None:
        self._thread = threading.Thread(target=self._receiver.capture)
        self._thread.setDaemon(True)
        self._thread.start()

    def connect(
        self, websocket: WebSocket, task_id: UUID, loop: asyncio.AbstractEventLoop
    ) -> UUID:
        connection_id = uuid.uuid4()
        self._connections[task_id][connection_id] = (websocket, loop)
        self._connections_id[connection_id] = task_id
        return connection_id

    def disconnect(self, connection_id: UUID) -> None:
        task_id = self._connections_id[connection_id]
        del self._connections[task_id][connection_id]

    def callback(self, event: dict) -> None:
        self._state.event(event)
        if "uuid" in event:
            for websocket, loop in self._connections[event["uuid"]].values():
                loop.call_soon_threadsafe(
                    websocket.send_json, schemas.TaskData(**event).dict()
                )


celery_events_listener = CeleryEventsListener(celery_app)
celery_events_listener.start()


@router.websocket_route("/ws/")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    task_id = websocket.query_params["uuid"]
    task = celery_app.AsyncResult(task_id)
    await websocket.send_json(task.get())

    connection_id = celery_events_listener.connect(
        websocket, UUID(task_id), asyncio.get_event_loop()
    )

    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        celery_events_listener.disconnect(connection_id)
