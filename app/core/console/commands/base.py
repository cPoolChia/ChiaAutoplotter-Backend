from __future__ import annotations
from app import schemas

from typing import TYPE_CHECKING, Optional, Generic, TypeVar
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ..connection_manager import ConnectionManager

_T = TypeVar("_T")


class ConsoleExecutionError(Exception):
    ...


class BaseCommand(ABC, Generic[_T]):
    _command: str

    def __init__(self, connection: ConnectionManager) -> None:
        self._connection = connection

    def __call__(self, *, cd: Optional[str] = None, **kwargs: str) -> _T:
        log = self._connection.execute("; ".join(self._create_command(cd=cd, **kwargs)))
        return self._process_stdout(log)

    @classmethod
    def _create_command(cls, *, cd: Optional[str] = None, **kwargs: str) -> list[str]:
        command = kwargs.get("command", cls._command)
        if cd is not None:
            return [f"cd {cd}", command]
        return [command]

    @classmethod
    def _generate_params(
        cls,
        kwargs: dict[str, str],
        *,
        start: str = "-",
        separator: str = " ",
        key_separator: str = " ",
    ) -> str:
        return separator.join(
            f"{start}{k}{key_separator}{v}" for k, v in kwargs.items()
        )

    def _process_stdout(self, log: schemas.ConsoleLog) -> _T:
        if log.stderr != "":
            raise ConsoleExecutionError(log)
        return None  # type: ignore
