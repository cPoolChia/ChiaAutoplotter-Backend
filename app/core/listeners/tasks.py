from fastapi import WebSocket
from app import schemas
from celery import Celery
from fastapi.logger import logger

from uuid import UUID
import uuid
import threading
import asyncio
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
            for websocket, loop in self._connections[UUID(event["uuid"])].values():
                loop.create_task(websocket.send_json(schemas.TaskData(**event).dict()))
        for websocket, loop in self._connections[None].values():
            loop.create_task(websocket.send_json(schemas.TaskData(**event).dict()))
