from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi_utils.api_model import APIModel

from pydantic import Field


class UserCreate(APIModel):
    nickname: str = Field(
        regex=r"^([A-Za-zÄäÖöÜüß].{0}[A-Za-z0-9._ÄäÖöÜüß]{0,17}.[^._])$", max_length=20
    )
    password: str = Field(
        regex=r'^(?!.*[ .])(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,32}(?=.+[!&$%&?"]){0}.*$',  # https://regex101.com/
        max_length=50,
    )


class UserUpdate(APIModel):
    ...


class UserReturn(APIModel):
    id: UUID
    nickname: str
    created: datetime
