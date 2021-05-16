from app.core.console.connection_manager import ConnectionManager

from .base import BaseChiaCommand
from .plots import ChiaPlotsCommand


class ChiaCommand(BaseChiaCommand[None]):
    _command = "chia"

    def __init__(self, connection: ConnectionManager) -> None:
        super().__init__(connection)
        self.plots = ChiaPlotsCommand(connection)

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> None:
        super()._process_stdout(stdout, stderr)