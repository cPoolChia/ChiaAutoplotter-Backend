from __future__ import annotations

from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ..connection_manager import ConnectionManager


class BaseCommand(ABC):
    command: str

    def __init__(self, connection: ConnectionManager) -> None:
        self._connection = connection

    def __call__(self, *args: str, **kwargs: str) -> Any:
        stdout, stderr = self._connection.execute(
            f"{self.command} {' '.join(args)}"
            + (
                " ".join(f"--{k}={v}" for k, v in kwargs.items())
                if kwargs != {}
                else ""
            )
        )

        self._process_stdout(stdout, stderr)

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> Any:
        if stderr != b"":
            raise RuntimeError(stderr)
