from __future__ import annotations

from typing import TYPE_CHECKING
from .base import BaseCommand
from .folder_commands import *

if TYPE_CHECKING:
    from ..connection_manager import ConnectionManager


class CommandList:
    def __init__(self, connection: ConnectionManager) -> None:
        self.cd = ChangeDirectoryCommand(connection)
        self.ls = ListCommand(connection)