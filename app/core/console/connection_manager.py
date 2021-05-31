from __future__ import annotations
from typing import Any, Callable, Optional, Type, BinaryIO, TypedDict
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
    class TaskRuntimeError(RuntimeError):
        ...

    def __init__(
        self,
        server: schemas.ServerReturn,
        task: celery.AsyncTask,
        *,
        log_collector: Optional[ConsoleLogCollector] = None,
        on_failed: Optional[Callable[[], None]] = None,
        on_success: Optional[Callable[[], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        self._server = server
        self.log_collector = log_collector or ConsoleLogCollector()
        self._task = task
        self._on_failed = on_failed
        self._on_success = on_success
        self._on_finished = on_finished
        self._failed_data = None

        crud.CRUDBase.set_object_listener(deps.get_object_update_listener())

    @property
    def failed_data(self) -> Optional[dict[str, Any]]:
        return self._failed_data

    def set_failed(self, **value: Any) -> None:
        self._failed_data = value
        self.log_collector.update_log(stdout=value.get("info", "").encode("utf8"))
        self._task.send_event("task-failed", data=self._failed_data)

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
        with self.log_collector:
            try:
                self.log_collector.update_log(
                    command=f"ssh {self._server.username}@{self._server.hostname}"
                )
                if ":" in self._server.hostname:
                    host, port = self._server.hostname.split(":")[:2]
                else:
                    host, port = self._server.hostname, "22"
                self._ssh_client.connect(
                    hostname=host,
                    port=int(port),
                    username=self._server.username,
                    password=self._server.password,
                )
            except Exception as connection_error:
                self.log_collector.update_log(
                    stdout=(
                        f"{connection_error.__class__.__name__}: " f"{connection_error}"
                    ).encode("utf8")
                )
                self._callback_failed()
                self._callback_finished()
                self.set_failed(
                    info=f"Error: {connection_error}",
                    error_type=connection_error.__class__.__name__,
                    console=self.log_collector.get(),
                )
                raise
            else:
                self.log_collector.update_log(stdout=b"Connected successfully")

        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        if exception_type is not None or exception_value is not None:
            self.set_failed(
                info=f"Error: {exception_value}",
                error_type=exception_type.__name__,
                console=self.log_collector.get(),
            )
            self._callback_failed()
        else:
            self._callback_success()

        self._callback_finished()
        self._ssh_client.close()

        return True

    def execute(self, command: str) -> schemas.ConsoleLog:
        BUFFER_SIZE = -1
        with self.log_collector:
            log_data = self.log_collector.update_log(command=command)
            stdin, stdout, stderr = self._ssh_client.exec_command(command, BUFFER_SIZE)
            stdout.channel.set_combine_stderr(True)

            for line in stdout:
                log_data = self.log_collector.update_log(stdout=(line).encode("utf-8"))
                self._task.send_event(
                    "task-update",
                    data={
                        "info": f"Executed: {command}",
                        "console": self.log_collector.get(),
                    },
                )

        return log_data

    def warn(self, message: str) -> None:
        self.log_collector.update_log(
            stdout=f"\nExecution Warning: {message}\n".encode("utf-8")
        )
        self._task.send_event(
            "task-update",
            data={
                "info": "Warning",
                "console": self.log_collector.get(),
            },
        )

    @property
    def command(self) -> CommandList:
        return CommandList(self)