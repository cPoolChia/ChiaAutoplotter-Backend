from typing import Optional, TypeVar
from abc import ABC
from .base import BaseChiaCommand


class ChiaInstallCommand(BaseChiaCommand[None]):
    _command = 'echo "done"'

    @classmethod
    def _create_command(cls, *, cd: Optional[str] = None, **kwargs: str) -> list[str]:
        orig_command = super()._create_command(cd=cd, **kwargs)
        return (
            orig_command[:-2]
            + [
                "sudo apt-get update",
                "sudo apt-get upgrade -y",
                "sudo apt install git -y",
                "git clone https://github.com/Chia-Network/chia-blockchain.git "
                "-b latest --recurse-submodules",
                "cd chia-blockchain",
                "sh install.sh",
            ]
            + orig_command[-2:]
        )

    def _process_stdout(self, stdout: bytes, stderr: bytes) -> None:
        return None
