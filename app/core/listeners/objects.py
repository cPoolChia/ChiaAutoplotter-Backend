from asyncio.events import AbstractEventLoop
from app import models, crud, db
import asyncio
import collections
from uuid import UUID
from fastapi import WebSocket
from pydantic import BaseModel
from typing import Type

import warnings
from .base import BaseListener


class ObjectUpdateListener(BaseListener):
    def notify_change(
        self, db_obj: db.Base, schema: Type[BaseModel], change_type: str
    ) -> None:
        for websocket, loop in self._connections_unfiltered.values():
            loop.create_task(
                websocket.send_json(
                    {
                        "table": db_obj.__tablename__,
                        "type": change_type,
                        "obj": schema.from_orm(db_obj).dict(),  # type: ignore
                    }
                )
            )
