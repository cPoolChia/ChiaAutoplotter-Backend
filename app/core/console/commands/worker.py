from typing import Optional
from app.core.console.commands.base import BaseCommand


class WorkerStartCommand(BaseCommand[None]):
    _command = "poetry run uvicorn app:app --reload --host 0.0.0.0 --log-level debug"

    def __call__(self, *, cd: Optional[str] = None, **kwargs: str) -> None:
        commands = [
            "sudo apt-get update",
            "sudo apt-get upgrade -y",
            "sudo apt install git -y",
            "git clone https://github.com/cPoolChia/ChiaAutoplotter-Worker.git",
            "sudo apt install python3.9",
            "python3.9 get-pip.py",
            "python3.9 -m pip install poetry",
            "poetry install",
        ]
        for command in commands:
            super().__call__(command=command)

        return super().__call__(cd="/root/ChiaAutoplotter-Worker", **kwargs)
