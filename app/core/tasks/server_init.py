from typing import Any, Callable, TypedDict

import celery
import paramiko
import time
from uuid import UUID
from app import schemas, crud
from app.api import deps
from app.celery import celery as celery_app
from sqlalchemy.orm import Session


class ConsoleLog(TypedDict):
    command: str
    stdout: str
    stderr: str
    time: float


class ConsoleGatherer:
    def __init__(self) -> None:
        self._data: list[ConsoleLog] = []

    def add(self, stdout: bytes, stderr: bytes, command: str) -> None:
        self._data.append(
            {
                "command": command,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
                "time": time.time(),
            }
        )

    def get(self) -> list[ConsoleLog]:
        return self._data


@celery_app.task(bind=True)
def init_server_connect(
    self: celery.Task,
    server_id: UUID,
    *,
    db_factory: Callable[[], Session] = lambda: next(deps.get_db()),
) -> Any:
    db = db_factory()
    console = ConsoleGatherer()

    for i in range(15):
        time.sleep(1)
        self.send_event(
            "task-update",
            data={"info": f"Starting {i+1} ({server_id})", "console": console.get()},
        )

    server = crud.server.get(db, id=server_id)

    if server is None:
        raise RuntimeError(
            f"Can not find a server data with id {server_id} in a database"
        )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=server.hostname, username=server.username, password=server.password
    )

    self.send_event("task-update", data={"info": "Connected", "console": console.get()})

    def execute_shell(command: str) -> None:
        stdin, stdout, stderr = client.exec_command(command)
        console.add(stdout.read(), stderr.read(), command)

        self.send_event(
            "task-update",
            data={"info": f"Executed: {command}", "console": console.get()},
        )
        time.sleep(2)

    execute_shell("ls")
    execute_shell("cd /plots")
    execute_shell("ls")

    client.close()

    return {"info": "done", "console": console.get()}
