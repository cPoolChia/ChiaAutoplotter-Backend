from __future__ import annotations

from typing import Any, TYPE_CHECKING, Optional, Generic, TypeVar
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ..connection_manager import ConnectionManager

_T = TypeVar("_T")


class BaseCommand(ABC, Generic[_T]):
    _command: str

    def __init__(self, connection: ConnectionManager) -> None:
        self._connection = connection

    def __call__(self, *args: str, **kwargs: str) -> _T:
        stdout, stderr = self._connection.execute(
            "; ".join(self._create_command(*args, **kwargs))
        )
        return self._process_stdout(stdout, stderr)

    @classmethod
    def _create_command(cls, *args: str, **kwargs: str) -> list[str]:
        cd: Optional[str] = kwargs.get("cd", None)
        main_command = f"{cls._command} {' '.join(args)}"
        if cd is not None:
            return [f"cd {cd}", main_command]
        return [main_command]

    @abstractmethod
    def _process_stdout(self, stdout: bytes, stderr: bytes) -> _T:
        if stderr != b"":
            raise RuntimeError(stderr)
        return None  # type: ignore
