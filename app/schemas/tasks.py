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
        if not isinstance(v, str):
            return v
        if isinstance(v, Exception):
            return {"value": str(v), "error": v.__class__.__name__}
        try:
            return json.loads(v.replace("'", '"').replace("\n", r"\n"))
        except json.JSONDecodeError as e:

            return {"value": v, "error": str(e)}
