from typing import TYPE_CHECKING
from datetime import datetime
import uuid
import random
import string

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from fastapi_utils.guid_type import GUID
from app.db.base_class import Base

from app.models.plot import Plot

if TYPE_CHECKING:
    from .plot_queue import PlotQueue, Directory


def generate_random_password(length: int) -> str:
    return "".join(
        random.choice(string.ascii_letters + string.ascii_letters)
        for _ in range(length)
    )


class Server(Base):
    name = Column(String(200), nullable=False, index=True, unique=True)
    hostname = Column(String(200), nullable=False, unique=True)
    username = Column(String(30), nullable=False)
    password = Column(String(200), nullable=False)
    pool_key = Column(String(100), nullable=False)
    farmer_key = Column(String(100), nullable=False)
    worker_password = Column(
        String(18), nullable=False, default=lambda: generate_random_password(18)
    )
    worker_port = Column(Integer, nullable=False, default=8000)
    worker_version = Column(String(40), nullable=False, default="pending")
    status = Column(String(40), default="pending")
    directories = relationship("Directory", uselist=True, back_populates="server")
