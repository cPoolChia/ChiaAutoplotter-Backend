from typing import Optional
from uuid import UUID

from enum import Enum
from datetime import datetime
from fastapi_utils.api_model import APIModel
from pydantic import Field

from .plot import PlotReturn


class ServerStatus(Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    FAILED = "failed"


class ServerCreate(APIModel):
    name: str
    hostname: str
    worker_port: int
    username: str
    password: str
    pool_key: str
    farmer_key: str


class ServerCreateExtended(ServerCreate):
    directories: set[str] = []


class ServerUpdate(APIModel):
    name: Optional[str] = Field()
    hostname: Optional[str] = Field()
    worker_port: Optional[int] = Field()
    username: Optional[str] = Field()
    password: Optional[str] = Field()
    pool_key: Optional[str] = Field()
    farmer_key: Optional[str] = Field()


class ServerReturn(APIModel):
    id: UUID
    name: str
    hostname: str
    worker_port: int
    worker_version: str
    username: str
    password: str
    pool_key: str
    farmer_key: str
    created: datetime
    status: ServerStatus
