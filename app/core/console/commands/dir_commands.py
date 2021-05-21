from app import schemas
from typing import Any, Optional
from .base import BaseCommand


class ListDirectoryCommand(BaseCommand[set[str]]):
    _command = "ls"

    def _process_stdout(self, log: schemas.ConsoleLog) -> set[str]:
        super()._process_stdout(log)
        return set(log.stdout.split())


class CreateDirectoryCommand(BaseCommand[bool]):
    _command = "mkdir"

    @classmethod
    def _create_command(
        cls, *, cd: Optional[str] = None, dirname: str = "", **kwargs: str
    ) -> list[str]:
        command = super()._create_command(cd=cd, **kwargs)
        return command[:-1] + [command[-1] + " " + dirname]

    def _process_stdout(self, log: schemas.ConsoleLog) -> bool:
        if "File exists" in log.stdout:
            return False
        super()._process_stdout(log)
        return True


class RemoveDirectoryCommand(BaseCommand[None]):
    _command = "rm -rf"

    @classmethod
    def _create_command(
        cls, *, cd: Optional[str] = None, dirname: str = "", **kwargs: str
    ) -> list[str]:
        command = super()._create_command(cd=cd, **kwargs)
        return command[:-1] + [command[-1] + " " + dirname]