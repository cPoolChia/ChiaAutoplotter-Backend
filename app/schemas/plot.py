from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from enum import Enum
from fastapi_utils.api_model import APIModel

from .plot_queue import PlotQueueReturn


class PlotStatus(Enum):
    PENDING = "pending"
    PLOTTING = "plotting"
    PLOTTED = "plotted"
    TRANSFERRING = "transferring"
    LOST = "lost"


class PlotCreate(APIModel):
    name: str
    location: str
    created_queue_id: Optional[UUID]
    located_directory_id: UUID
    status: PlotStatus = PlotStatus.PLOTTING


class PlotUpdate(APIModel):
    located_server_id: Optional[UUID] = None
    status: Optional[PlotStatus] = None


class PlotReturn(APIModel):
    id: UUID
    name: str
    location: str
    created_queue_id: Optional[UUID]
    located_directory_id: UUID
    created: datetime
    status: PlotStatus