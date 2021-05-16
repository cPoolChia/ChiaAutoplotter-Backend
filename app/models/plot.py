from typing import TYPE_CHECKING
from datetime import datetime
import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from fastapi_utils.guid_type import GUID
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models import Server


class Plot(Base):
    name = Column(String(200), nullable=False)
    created_server_id = Column(GUID, ForeignKey("server.id"), index=True, nullable=True)
    located_server_id = Column(
        GUID, ForeignKey("server.id"), index=True, nullable=False
    )
    created_server = relationship(
        "Server",
        foreign_keys=[created_server_id],
        # back_populates="Server.created_plots",
    )
    located_server = relationship(
        "Server",
        foreign_keys=[located_server_id],
        # back_populates="Server.located_plots",
    )
    status = Column(String(30), nullable=False, default="plotting")
