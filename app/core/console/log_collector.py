from typing import Any, Optional
from app import schemas

import warnings


class ConsoleLogCollector:
    def __init__(self) -> None:
        self._data: list[schemas.ConsoleLog] = []
        self._data.append(schemas.ConsoleLog(command="Starting task execution..."))

    def __enter__(self) -> None:
        self._data.append(schemas.ConsoleLog())

    def __exit__(self, *args: Any) -> None:
        return

    def update_log(
        self, stdout: bytes = b"", command: Optional[str] = None
    ) -> schemas.ConsoleLog:
        if command is not None:
            self._data[-1].command = command
        self._data[-1].stdout += stdout.decode("utf-8")
        return self._data[-1]

    def get(self) -> list[dict[str, Any]]:
        return [entry.dict() for entry in self._data]