from app.core.console.connection_manager import ConnectionManager
from .base import BaseChiaCommand


class ChiaPlotsCreateCommand(BaseChiaCommand[None]):
    _command = "chia plots create"

    @classmethod
    def _create_command(cls, *args: str, **kwargs: str) -> list[str]:
        orig_command = super()._create_command(*args, **kwargs)
        create_dir = kwargs.get("create_dir")
        plot_dir = kwargs.get("plot_dir")
        pool_key = kwargs.get("pool_key")
        farmer_key = kwargs.get("farmer_key")
        plots_amount = kwargs.get("plots_amount")
        command_params = (
            f"-t {plot_dir} "
            f"-d {create_dir} "
            f"-n {plots_amount} "
            f"-p {pool_key} "
            f"-f {farmer_key}"
        )
        return orig_command[:-1] + [f"{orig_command[-1]} {command_params}"]

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> None:
        super()._process_stdout(stdout, stderr)


class ChiaPlotsCommand(BaseChiaCommand[None]):
    _command = "chia plots"

    def __init__(self, connection: ConnectionManager) -> None:
        super().__init__(connection)
        self.create = ChiaPlotsCreateCommand(connection)

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> None:
        super()._process_stdout(stdout, stderr)