from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from enum import Enum
from fastapi_utils.api_model import APIModel

from .plot_queue import PlotQueueReturn


class DirectoryStatus(Enum):
    PENDING = "pending"
    MONITORING = "monitoring"
    FAILED = "failed"


class DirectoryCreate(APIModel):
    location: str


class DirectoryCreateExtended(DirectoryCreate):
    server_id: UUID


class DirectoryUpdate(APIModel):
    ...


class DirectoryReturn(APIModel):
    id: UUID
    location: str
    server_id: UUID
    created: datetime
    status: DirectoryStatus
    disk_size: Optional[int]
    disk_taken: Optional[int]