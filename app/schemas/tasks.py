from typing import Any
from pydantic import BaseModel, validator
from fastapi_utils.api_model import APIModel

import json
import time

from pydantic.fields import Field


class TaskData(APIModel):
    uuid: str
    state: str = "UNKNOWN"
    timestamp: float = Field(default_factory=time.time)
    clock: int = 0
    data: Any = {}
