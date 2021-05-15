from typing import Any
from .base import BaseCommand


class ChangeDirectoryCommand(BaseCommand):
    command = "cd"


class ListCommand(BaseCommand):
    command = "ls"

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> list[str]:
        super()._process_stdout(stdout, stderr)
        return stdout.decode("utf8").split()