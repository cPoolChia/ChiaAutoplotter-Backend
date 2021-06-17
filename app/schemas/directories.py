import uuid
from pydantic import BaseModel
from typing import Optional


class PlotData(BaseModel):
    name: str
    plotting: bool
    queue: Optional[uuid.UUID]

    def __hash__(self) -> int:
        return hash((type(self),) + tuple(self.__dict__.values()))


class DiskData(BaseModel):
    total: int
    free: int
    used: int


class DirInfo(BaseModel):
    plots: set[PlotData] = set()
    disk_size: Optional[DiskData] = None
