from abc import ABC
from app import models, crud, db
import asyncio
import collections
from uuid import UUID
import uuid
from fastapi import WebSocket
from pydantic import BaseModel
from typing import Optional, Type


class BaseListener(ABC):
    def __init__(self) -> None:
        self._connections: dict[
            Optional[UUID], dict[UUID, tuple[WebSocket, asyncio.AbstractEventLoop]]
        ] = collections.defaultdict(lambda: {})
        self._connections_id: dict[UUID, Optional[UUID]] = {}

    @property
    def _connections_unfiltered(
        self,
    ) -> dict[UUID, tuple[WebSocket, asyncio.AbstractEventLoop]]:
        return self._connections[None]

    def connect(
        self,
        websocket: WebSocket,
        filter_id: Optional[UUID] = None,
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop(),
    ) -> UUID:
        connection_id = uuid.uuid4()
        self._connections[filter_id][connection_id] = (websocket, loop)
        self._connections_id[connection_id] = filter_id

        return connection_id

    def disconnect(self, connection_id: UUID) -> None:
        task_id = self._connections_id[connection_id]
        del self._connections[task_id][connection_id]
        del self._connections_id[connection_id]