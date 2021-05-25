from typing import TYPE_CHECKING
from datetime import datetime
import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from fastapi_utils.guid_type import GUID
from app.db.base_class import Base
from sqlalchemy.dialects.mysql import DATETIME

if TYPE_CHECKING:
    from app.models import Plot, Directory


class Transfer(Base):
    starting_directory_id = Column(GUID, ForeignKey("directory.id"), nullable=False)
    starting_directory = relationship("Directory", foreign_keys=[starting_directory_id])
    destination_directory_id = Column(GUID, ForeignKey("directory.id"), nullable=False)
    destination_directory = relationship(
        "Directory", foreign_keys=[destination_directory_id]
    )
    plot_id = Column(GUID, ForeignKey("plot.id"), nullable=False)
    plot = relationship("Plot", foreign_keys=[plot_id])
    transfer_task_id = Column(GUID, nullable=True)
    finished = Column(DATETIME(fsp=6), nullable=True, default=None)
    status = Column(String(40), default="pending", nullable=False)
