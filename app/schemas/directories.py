import uuid
from pydantic import BaseModel
from typing import Optional


class PlotData(BaseModel):
    name: str
    plotting: bool
    queue: Optional[uuid.UUID]

    class Config:
        frozen = True


class DiskData(BaseModel):
    total: int
    free: int
    used: int


class DirInfo(BaseModel):
    plots: set[PlotData] = set()
    disk_size: Optional[DiskData] = None
