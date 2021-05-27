from typing import Any, Optional
from fastapi import WebSocket
from app import schemas
from celery import Celery
from fastapi.logger import logger

from uuid import UUID
import uuid
import threading
import asyncio
import time
import collections

from .base import BaseListener


class TaskEventsListener(BaseListener):
    def __init__(self, app: Celery) -> None:
        super().__init__()
        self._app = app
        # self._last_events: dict[UUID, schemas.TaskData] = {}

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

    # def connect(
    #     self,
    #     websocket: WebSocket,
    #     filter_id: Optional[UUID] = None,
    #     loop: asyncio.AbstractEventLoop = asyncio.get_event_loop(),
    # ) -> UUID:
    #     connection_id = super().connect(websocket, filter_id=filter_id, loop=loop)
    #     if filter_id is not None and filter_id in self._last_events:
    #         loop.create_task(websocket.send_json(self._last_events[filter_id]))
    #     return connection_id

    def callback(self, event: dict) -> None:
        self._state.event(event)
        if "uuid" in event:
            event_id = UUID(event["uuid"])
            if "result" not in event:
                task_data = schemas.TaskData(**event).dict()
            else:
                task = self._app.AsyncResult(event["uuid"])
                task_data = schemas.TaskData(
                    uuid=event["uuid"],
                    state=task.state,
                    timestamp=time.time(),
                    data=task.info,
                ).dict()
            # self._last_events[event_id] = task_data

            for websocket, loop in self._connections[event_id].values():
                loop.create_task(websocket.send_json(task_data))
            for websocket, loop in self._connections[None].values():
                loop.create_task(websocket.send_json(task_data))
