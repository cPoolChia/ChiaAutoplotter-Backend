from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from enum import Enum
from fastapi_utils.api_model import APIModel


class PlotQueueStatus(Enum):
    PENDING = "pending"
    PLOTTING = "plotting"
    WAITING = "waiting"
    FAILED = "failed"
    PAUSED = "paused"


class PlotQueueCreate(APIModel):
    server_id: UUID
    temp_dir_id: UUID
    final_dir_id: UUID
    autoplot: bool = True
    plots_amount: int
    k: int = 32
    threads: int = 2
    ram: int = 4608


class PlottingData(APIModel):
    final_dir: str
    temp_dir: str
    queue_id: UUID
    pool_key: str
    farmer_key: str
    plots_amount: int
    k: int
    threads: int
    ram: int


class PlottingReturn(APIModel):
    id: UUID
    status_code: Optional[int] = None
    finished: bool = False


class PlotQueueUpdate(APIModel):
    temp_dir_id: Optional[UUID] = None
    final_dir_id: Optional[UUID] = None
    plots_amount: Optional[int] = None
    autoplot: Optional[bool] = None
    k: Optional[int] = None
    threads: Optional[int] = None
    ram: Optional[int] = None


class PlotQueueReturn(APIModel):
    id: UUID
    server_id: UUID
    temp_dir_id: UUID
    final_dir_id: UUID
    plotting_started: Optional[datetime]
    autoplot: bool
    plots_amount: int
    k: int
    threads: int
    ram: int
    created: datetime
    status: PlotQueueStatus
