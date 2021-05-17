from __future__ import annotations

from typing import TYPE_CHECKING
from .base import BaseCommand
from .dir_commands import *
from .chia import *

if TYPE_CHECKING:
    from ..connection_manager import ConnectionManager


class CommandList:
    def __init__(self, connection: ConnectionManager) -> None:
        self.ls = ListDirectoryCommand(connection)
        self.chia = ChiaCommand(connection)