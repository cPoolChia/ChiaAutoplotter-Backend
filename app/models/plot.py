from typing import TYPE_CHECKING
from datetime import datetime
import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from fastapi_utils.guid_type import GUID
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models import PlotQueue, Directory


class Plot(Base):
    name = Column(String(200), nullable=False, index=True, unique=True)
    location = Column(String(200), nullable=False)
    created_queue_id = Column(
        GUID, ForeignKey("plotqueue.id"), index=True, nullable=True
    )
    located_directory_id = Column(
        GUID, ForeignKey("directory.id"), index=True, nullable=False
    )
    created_queue = relationship("PlotQueue", foreign_keys=[created_queue_id])
    located_directory = relationship("Directory", foreign_keys=[located_directory_id])
    status = Column(String(40), nullable=False, default="pending")
