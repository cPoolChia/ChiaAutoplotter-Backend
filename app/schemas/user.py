from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi_utils.api_model import APIModel

from pydantic import Field


class UserCreate(APIModel):
    nickname: str
    password: str


class UserUpdate(APIModel):
    password: str


class UserReturn(APIModel):
    id: UUID
    nickname: str
    created: datetime
