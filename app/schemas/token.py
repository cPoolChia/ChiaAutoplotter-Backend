from datetime import datetime
from typing import Optional, Pattern, Annotated
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class BaseTokenPayload(BaseModel):
    exp: datetime


class AuthTokenPayload(BaseTokenPayload):
    sub: UUID