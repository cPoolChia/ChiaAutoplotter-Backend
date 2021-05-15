from typing import Any
from app import schemas


class ConsoleLogCollector:
    def __init__(self) -> None:
        self._data: list[schemas.ConsoleLog] = []

    def add(self, stdout: bytes, stderr: bytes, command: str) -> None:
        self._data.append(
            schemas.ConsoleLog(
                command=command,
                stdout=stdout.decode("utf-8"),
                stderr=stderr.decode("utf-8"),
            )
        )

    def get(self) -> list[dict[str, Any]]:
        return [entry.dict() for entry in self._data]