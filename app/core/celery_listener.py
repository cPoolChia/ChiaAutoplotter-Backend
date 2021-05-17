from fastapi import WebSocket
from app import schemas
from celery import Celery
from fastapi.logger import logger

from uuid import UUID
import uuid
import threading
import asyncio
import collections


class CeleryEventsListener:
    def __init__(self, app: Celery) -> None:
        self._app = app
        self._connections: dict[
            UUID, dict[UUID, tuple[WebSocket, asyncio.AbstractEventLoop]]
        ] = collections.defaultdict(lambda: {})
        self._connections_id: dict[UUID, UUID] = {}

    def start(self) -> None:
        self._state = self._app.events.State()

        with self._app.connection() as connection:
            self._receiver = self._app.events.Receiver(
                connection,
                handlers={
                    "*": self.callback,
                },
            )

            self._receiver.capture(limit=None, timeout=None, wakeup=True)

    def start_threaded(self) -> None:
        self._thread = threading.Thread(target=self.start)
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
            for websocket, loop in self._connections[UUID(event["uuid"])].values():
                loop.create_task(websocket.send_json(schemas.TaskData(**event).dict()))
