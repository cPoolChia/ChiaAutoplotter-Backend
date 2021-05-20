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

    def callback(self, event: dict) -> None:
        self._state.event(event)
        if "uuid" in event:
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
            for websocket, loop in self._connections[UUID(event["uuid"])].values():
                loop.create_task(websocket.send_json(task_data))
            for websocket, loop in self._connections[None].values():
                loop.create_task(websocket.send_json(task_data))
