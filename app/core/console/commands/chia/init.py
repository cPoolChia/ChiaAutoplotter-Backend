from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from .base import BaseChiaCommand
from app.core.config import settings

if TYPE_CHECKING:
    from app.core.console.connection_manager import ConnectionManagers


class ChiaInitCommand(BaseChiaCommand[None]):
    _command = "chia init"

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> None:
        super()._process_stdout(stdout, stderr)