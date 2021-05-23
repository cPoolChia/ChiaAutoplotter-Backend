from typing import TYPE_CHECKING
from datetime import datetime
import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from fastapi_utils.guid_type import GUID
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models import Server, PlotQueue, Plot


class Directory(Base):
    location = Column(String(200), nullable=False)
    server_id = Column(GUID, ForeignKey("server.id"), index=True, nullable=False)
    server = relationship("Server", foreign_keys=[server_id])
    plots = relationship("Plot", use_list=True)
    status = Column(String(40), nullable=False, default="pending")
    disk_size = Column(Integer, nullable=True)
    disk_taken = Column(Integer, nullable=True)
