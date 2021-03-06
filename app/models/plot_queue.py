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
    from app.models import Server, Directory


class PlotQueue(Base):
    server_id = Column(GUID, ForeignKey("server.id"), index=True, nullable=False)
    server = relationship("Server", foreign_keys=[server_id])
    execution_id = Column(GUID, default=None)

    final_dir_id = Column(GUID, ForeignKey("directory.id"), nullable=False)
    temp_dir_id = Column(GUID, ForeignKey("directory.id"), nullable=False)
    final_dir = relationship("Directory", foreign_keys=[final_dir_id])
    temp_dir = relationship("Directory", foreign_keys=[temp_dir_id])

    plots_amount = Column(Integer, nullable=False)
    k = Column(Integer, nullable=False)
    threads = Column(Integer, nullable=False)
    ram = Column(Integer, nullable=False)
    
    autoplot = Column(Boolean, nullable=False, default=True)
    plotting_started = Column(DATETIME(fsp=6), default=None, nullable=True)

    status = Column(String(40), nullable=False, default="pending")
