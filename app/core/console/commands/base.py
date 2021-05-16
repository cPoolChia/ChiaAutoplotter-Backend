from __future__ import annotations

from typing import Any, TYPE_CHECKING, Optional, Generic, TypeVar
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ..connection_manager import ConnectionManager

_T = TypeVar("_T")


class BaseCommand(ABC, Generic[_T]):
    command: str

    def __init__(self, connection: ConnectionManager) -> None:
        self._connection = connection

    def __call__(self, *args: str, **kwargs: str) -> _T:
        stdout, stderr = self._connection.execute(self._create_command(*args, **kwargs))
        return self._process_stdout(stdout, stderr)

    @classmethod
    def _create_command(cls, *args: str, **kwargs: str) -> str:
        cd: Optional[str] = kwargs.get("cd", None)
        cd_pre_command = f"cd {cd}; " if cd is not None else ""
        main_command = f"{cls.command} {' '.join(args)}"
        return cd_pre_command + main_command

    @abstractmethod
    def _process_stdout(self, stdout: bytes, stderr: bytes) -> _T:
        if stderr != b"":
            raise RuntimeError(stderr)
        return None  # type: ignore
