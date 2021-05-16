from typing import TYPE_CHECKING
from datetime import datetime
import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from fastapi_utils.guid_type import GUID
from app.db.base_class import Base

from app.models.plot import Plot


class Server(Base):
    hostname = Column(String(200), nullable=False)
    username = Column(String(30), nullable=False)
    password = Column(String(200), nullable=False)
    init_task_id = Column(GUID, nullable=True)
    status = Column(String(40), default="pending")

    located_plots = relationship(
        "Plot", foreign_keys=[Plot.created_server_id], uselist=True
    )
    created_plots = relationship(
        "Plot", foreign_keys=[Plot.located_server_id], uselist=True
    )
