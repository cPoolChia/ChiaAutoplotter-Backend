import threading
from app import db
from app.core.config import settings
from pydantic import BaseModel
from typing import Any, Type
from fastapi.encoders import jsonable_encoder

from .base import BaseListener
from kombu import Exchange, Queue, Connection
from kombu.mixins import ConsumerMixin
from kombu.pools import producers

import warnings

task_exchange = Exchange("tasks", type="direct")
task_queues = [Queue("default", task_exchange, routing_key="default")]


class ObjectUpdateListener(BaseListener, ConsumerMixin):
    def __init__(self) -> None:
        super().__init__()
        self.connection = Connection(settings.CELERY_BROKER)

    def __del__(self) -> None:
        self.connection.close()

    def start_threaded(self) -> None:
        self._thread = threading.Thread(target=self.run)
        self._thread.setDaemon(True)
        self._thread.start()

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(
                queues=task_queues,
                accept=["json"],
                callbacks=[self.process_task],
            )
        ]

    def process_task(self, body, message):
        for websocket, loop in self._connections_unfiltered.values():
            loop.create_task(websocket.send_json(body))
        message.ack()

    def send_as_task(self, connection, payload: Any) -> None:
        with producers[connection].acquire(block=True) as producer:
            producer.publish(
                payload,
                serializer="json",
                compression="bzip2",
                exchange=task_exchange,
                declare=[task_exchange],
                routing_key="default",
            )

    def notify_change(
        self, db_obj: db.Base, schema: Type[BaseModel], change_type: str
    ) -> None:
        content = jsonable_encoder(
            {
                "table": db_obj.__tablename__,
                "type": change_type,
                "obj": schema.from_orm(db_obj),  # type: ignore
            }
        )
        warnings.warn(f"{content}")
        self.send_as_task(self.connection, content)
