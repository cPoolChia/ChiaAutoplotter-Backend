from uuid import UUID

from enum import Enum
from datetime import datetime
from fastapi_utils.api_model import APIModel

from .plot import PlotReturn


class ServerStatus(Enum):
    PENDING = "pending"
    CONNECTED = "success"
    FAILED = "failed"


class ServerCreate(APIModel):
    hostname: str
    username: str
    password: str


class ServerUpdate(ServerCreate):
    ...


class ServerReturn(APIModel):
    id: UUID
    hostname: str
    username: str
    password: str
    init_task_id: UUID
    created: datetime
    status: ServerStatus
