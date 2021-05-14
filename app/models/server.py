from typing import TYPE_CHECKING
from datetime import datetime
import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from fastapi_utils.guid_type import GUID
from app.db.base_class import Base


class Server(Base):
    hostname = Column(String(200), nullable=False)
    nickname = Column(String(30), nullable=False)
    password = Column(String(200), nullable=False)
