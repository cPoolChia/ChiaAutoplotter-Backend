from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from .base import BaseChiaCommand
from app.core.config import settings

if TYPE_CHECKING:
    from app.core.console.connection_manager import ConnectionManager


class ChiaPlotsCreateCommand(BaseChiaCommand[None]):
    _command = "chia plots create"

    def __call__(
        self,
        *,
        cd: Optional[str] = None,
        create_dir: Optional[str] = None,
        plot_dir: str = "/root/plots",
        pool_key: str = settings.CHIA_POOL_KEY,
        farmer_key: str = settings.CHIA_FARMER_KEY,
        plots_amount: str = "1",
        **kwargs: str,
    ) -> None:
        return super().__call__(
            cd=cd,
            create_dir=create_dir,
            plot_dir=plot_dir,
            pool_key=pool_key,
            farmer_key=farmer_key,
            plots_amount=plots_amount,
            **kwargs,
        )

    @classmethod
    def _create_command(
        cls,
        *,
        cd: Optional[str] = None,
        create_dir: Optional[str] = None,
        plot_dir: str = "/root/plots",
        pool_key: str = settings.CHIA_POOL_KEY,
        farmer_key: str = settings.CHIA_FARMER_KEY,
        plots_amount: str = "1",
        **kwargs: str,
    ) -> list[str]:
        orig_command = super()._create_command(cd=cd)
        assert create_dir is not None, "create_dir should be passed"

        command_params = cls._generate_params(
            {
                "t": plot_dir,
                "d": create_dir,
                "n": plots_amount,
                "p": pool_key,
                "f": farmer_key,
            }
        )
        return orig_command[:-1] + [f"{orig_command[-1]} {command_params}"]

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> None:
        return None


class ChiaPlotsCommand(BaseChiaCommand[None]):
    _command = "chia plots"

    def __init__(self, connection: ConnectionManager) -> None:
        super().__init__(connection)
        self.create = ChiaPlotsCreateCommand(connection)

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> None:
        super()._process_stdout(stdout, stderr)