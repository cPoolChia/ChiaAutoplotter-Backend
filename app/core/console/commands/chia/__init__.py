from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .base import BaseChiaCommand
from .plots import ChiaPlotsCommand
from .install import ChiaInstallCommand
from .init import ChiaInitCommand

if TYPE_CHECKING:
    from app.core.console.connection_manager import ConnectionManager


class ChiaCommand(BaseChiaCommand[None]):
    _command = "chia"

    def __init__(self, connection: ConnectionManager) -> None:
        super().__init__(connection)
        self.plots = ChiaPlotsCommand(connection)
        self.install = ChiaInstallCommand(connection)
        self.init = ChiaInitCommand(connection)

    @classmethod
    def _create_command(cls, *, cd: Optional[str] = None, **kwargs: str) -> list[str]:
        main_command = f"{cls._command}"
        if cd is not None:
            return [f"cd {cd}", main_command]
        return [main_command]