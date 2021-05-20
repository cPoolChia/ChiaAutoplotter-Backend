from pydantic import BaseModel

import time


class ConsoleLog(BaseModel):
    command: str = ""
    stdout: str = ""
    time: float = time.time()