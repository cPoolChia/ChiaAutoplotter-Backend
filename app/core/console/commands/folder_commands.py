from typing import Any
from .base import BaseCommand


class ListDirectoryCommand(BaseCommand[set[str]]):
    _command = "ls"

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> set[str]:
        super()._process_stdout(stdout, stderr)
        return set(stdout.decode("utf8").split())