from pydantic import BaseModel

import time


class ConsoleLog(BaseModel):
    command: str
    stdout: str
    stderr: str
    time: float = time.time()