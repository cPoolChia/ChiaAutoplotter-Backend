from __future__ import annotations
from typing import Any, Optional, Type
from types import TracebackType

from sqlalchemy.orm.session import Session

from app import models, crud
from .log_collector import ConsoleLogCollector
from .commands import CommandList
import paramiko
import celery


class ConnectionManager:
    def __init__(
        self,
        server: models.Server,
        task: celery.AsyncTask,
        console_logger: ConsoleLogCollector,
        db: Session,
    ) -> None:
        self._server = server
        self._log_collector = console_logger
        self._task = task
        self._db = db

    def __enter__(self) -> ConnectionManager:
        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self._ssh_client.connect(
                hostname=self._server.hostname,
                username=self._server.username,
                password=self._server.password,
            )
        except paramiko.SSHException:
            crud.server.update(
                self._db, db_obj=self._server, obj_in={"status": "failed"}
            )
            raise

        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if exception_type is not None and exception_value is not None:
            self._task.send_event(
                "task-failed",
                data={
                    "info": f"Error: {exception_value}",
                    "error_type": exception_type.__name__,
                },
            )
            crud.server.update(
                self._db, db_obj=self._server, obj_in={"status": "failed"}
            )
        self._ssh_client.close()

    def execute(self, command: str) -> tuple[bytes, bytes]:
        stdin, stdout, stderr = self._ssh_client.exec_command(command)
        out_text = stdout.read()
        err_text = stderr.read()
        self._log_collector.add(out_text, err_text, command)

        self._task.send_event(
            "task-update",
            data={"info": f"Executed: {command}", "console": self._log_collector.get()},
        )

        return out_text, err_text

    @property
    def command(self) -> CommandList:
        return CommandList(self)