from typing import Any, Callable, TypedDict

import celery
import paramiko
import time
from uuid import UUID
from app import schemas, crud
from app.core import console
from app.api import deps
from app.celery import celery as celery_app
from sqlalchemy.orm import Session


@celery_app.task(bind=True)
def init_server_connect(
    self: celery.Task,
    server_id: UUID,
    *,
    db_factory: Callable[[], Session] = lambda: next(deps.get_db()),
) -> Any:
    db = db_factory()
    console_logger = console.ConsoleLogCollector()

    server = crud.server.get(db, id=server_id)

    if server is None:
        raise RuntimeError(
            f"Can not find a server data with id {server_id} in a database"
        )

    with console.ConnectionManager(server, self, console_logger) as connection:
        root_content = connection.command.ls()
        if "plots" in root_content:
            connection.command.ls(cd="/root/plots")

    return {"info": "done", "console": console_logger.get()}
