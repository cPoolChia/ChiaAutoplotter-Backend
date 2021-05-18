from typing import Any, Optional
from .base import BaseCommand


class ListDirectoryCommand(BaseCommand[set[str]]):
    _command = "ls"

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> set[str]:
        super()._process_stdout(stdout, stderr)
        return set(stdout.decode("utf8").split())


class CreateDirectoryCommand(BaseCommand[bool]):
    _command = "mkdir"

    @classmethod
    def _create_command(
        cls, *, cd: Optional[str] = None, dirname: str = "", **kwargs: str
    ) -> list[str]:
        command = super()._create_command(cd=cd, **kwargs)
        return command[:-1] + [command[-1] + " " + dirname]

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> bool:
        if b"File exists" in stderr:
            return False
        super()._process_stdout(stdout, stderr)
        return True