from uuid import UUID
from pydantic import BaseModel, ValidationError
from pydantic.generics import GenericModel
from typing import Any, Generic, TypeVar
from fastapi_utils.api_model import APIModel
from enum import Enum


class Msg(APIModel):
    msg: str


class Id(APIModel):
    id: UUID


class Error(APIModel):
    description: str


_T = TypeVar("_T")


class Table(GenericModel, Generic[_T]):
    amount: int
    items: list[_T]