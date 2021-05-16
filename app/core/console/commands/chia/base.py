from typing import TypeVar
from abc import ABC
from app.core.console.commands.base import BaseCommand


_T = TypeVar("_T")


class BaseChiaCommand(BaseCommand[_T], ABC):
    @classmethod
    def _create_command(cls, *args: str, **kwargs: str) -> list[str]:
        orig_command = super()._create_command(*args, **kwargs)
        return orig_command[:-1] + [". ./activate"] + [orig_command[-1]]