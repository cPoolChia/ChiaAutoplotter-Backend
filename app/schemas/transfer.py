from typing import Optional
from uuid import UUID

from enum import Enum
from datetime import datetime
from fastapi_utils.api_model import APIModel
from pydantic import Field

from .plot import PlotReturn


class TransferStatus(Enum):
    PENDING = "pending"
    TRANSFERING = "transfering"
    FINISHED = "finished"
    FAILED = "failed"


class TransferCreate(APIModel):
    destination_directory_id: UUID
    plot_id: UUID


class TransferCreateExtended(TransferCreate):
    starting_directory_id: UUID


class TransferUpdate(APIModel):
    ...


class TransferReturn(APIModel):
    id: UUID
    starting_directory_id: UUID
    destination_directory_id: UUID
    plot_id: UUID
    transfer_task_id: Optional[UUID]
    created: datetime
    finished: Optional[datetime]
    status: TransferStatus
