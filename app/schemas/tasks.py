from typing import Any
from pydantic import BaseModel, validator
from fastapi_utils.api_model import APIModel

import json


class TaskData(APIModel):
    uuid: str
    state: str
    timestamp: float
    clock: int = 0
    data: Any
    result: Any

    @validator("result")
    def json_result(cls, v: Any) -> Any:
        try:
            return json.loads(v.replace("'", '"'))
        except json.JSONDecodeError:
            return v