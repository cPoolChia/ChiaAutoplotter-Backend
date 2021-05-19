from typing import Optional
from uuid import UUID

from enum import Enum
from datetime import datetime
from fastapi_utils.api_model import APIModel

from .plot import PlotReturn


class ServerStatus(Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    FAILED = "failed"


class ServerCreate(APIModel):
    hostname: str
    username: str
    password: str


class ServerUpdate(APIModel):
    hostname: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class ServerReturn(APIModel):
    id: UUID
    hostname: str
    username: str
    password: str
    init_task_id: Optional[UUID]
    created: datetime
    status: ServerStatus
