from uuid import UUID

from enum import Enum
from datetime import datetime
from fastapi_utils.api_model import APIModel


class ServerStatus(Enum):
    pending = "pending"
    connected = "success"
    failed = "failed"


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
    created: datetime
    status: ServerStatus

class ServerReturnExtended(ServerReturn):
    plots: list[str] # TODO
    queues: list[str] # TODO