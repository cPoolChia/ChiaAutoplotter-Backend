from app import schemas
from typing import Optional, TypeVar
from abc import ABC
from app.core.console.commands.base import BaseCommand


class ChiaInstallCommand(BaseCommand[None]):
    _command = "sh install.sh"

    def __call__(self, *, cd: Optional[str], **kwargs: str) -> None:
        commands = [
            "sudo apt-get update",
            "sudo apt-get upgrade -y",
            "sudo apt install git -y",
            "sudo ufw allow 8000/tcp",
            "git clone https://github.com/Chia-Network/chia-blockchain.git "
            "-b latest --recurse-submodules",
        ]
        for command in commands:
            super().__call__(command=command)

        return super().__call__(cd="/root/chia-blockchain", **kwargs)
