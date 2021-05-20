from __future__ import annotations
from typing import Any, Callable, Optional, Type, BinaryIO
from types import TracebackType

from sqlalchemy.orm.session import Session

from app import models, crud, schemas
from app.api import deps
from .commands import CommandList
from .log_collector import ConsoleLogCollector
import paramiko
import celery
import warnings


class ConnectionManager:
    def __init__(
        self,
        server: models.Server,
        task: celery.AsyncTask,
        db: Session,
        *,
        on_failed: Optional[Callable[[], None]] = None,
        on_success: Optional[Callable[[], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        self._server = server
        self.log_collector = ConsoleLogCollector()
        self._task = task
        self._db = db
        self._on_failed = on_failed
        self._on_success = on_success
        self._on_finished = on_finished

        crud.CRUDBase.set_object_listener(deps.get_object_update_listener())

    def _callback_failed(self) -> None:
        if self._on_failed is not None:
            self._on_failed()

    def _callback_success(self) -> None:
        if self._on_success is not None:
            self._on_success()

    def _callback_finished(self) -> None:
        if self._on_finished is not None:
            self._on_finished()

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
            self._callback_failed()
            self._callback_finished()
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
            self._callback_failed()
        else:
            self._callback_success()

        self._callback_finished()
        self._ssh_client.close()
        self._db.close()

    def execute(self, command: str) -> schemas.ConsoleLog:
        with self.log_collector:
            log_data = self.log_collector.update_log(command=command)
            stdin, stdout, stderr = self._ssh_client.exec_command(command)

            send_event = lambda: self._task.send_event(
                "task-update",
                data={
                    "info": f"Executed: {command}",
                    "console": self.log_collector.get(),
                },
            )

            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    content = stdout.channel.recv(1024)
                    log_data = self.log_collector.update_log(stdout=content)
                    self._task.send_event(
                        "task-update",
                        data={
                            "info": f"Executed: {command}",
                            "console": self.log_collector.get(),
                        },
                    )

        return log_data

    @property
    def command(self) -> CommandList:
        return CommandList(self)