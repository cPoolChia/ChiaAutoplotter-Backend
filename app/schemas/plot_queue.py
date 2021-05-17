from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from enum import Enum
from fastapi_utils.api_model import APIModel


class PlotQueueCreate(BaseModel):
    server_id: UUID
    create_dir: str
    plot_dir: str
    pool_key: str
    farmer_key: str
    plots_amount: int


class PlotQueueUpdate(BaseModel):
    create_dir: Optional[str] = None
    plot_dir: Optional[str] = None
    pool_key: Optional[str] = None
    farmer_key: Optional[str] = None
    plots_amount: Optional[int] = None


class PlotQueueReturn(APIModel):
    id: UUID
    plot_task_id: UUID
    server_id: UUID
    create_dir: str
    plot_dir: str
    pool_key: str
    farmer_key: str
    plots_amount: int
    created: datetime
