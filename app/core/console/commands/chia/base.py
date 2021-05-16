from typing import Optional, TypeVar
from abc import ABC
from app.core.console.commands.base import BaseCommand


_T = TypeVar("_T")


class BaseChiaCommand(BaseCommand[_T], ABC):
    @classmethod
    def _create_command(cls, *, cd: Optional[str] = None, **kwargs: str) -> list[str]:
        orig_command = super()._create_command(cd=cd, **kwargs)
        return orig_command[:-1] + [". ./activate"] + [orig_command[-1]]