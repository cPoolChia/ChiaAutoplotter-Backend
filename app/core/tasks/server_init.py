from typing import Any, Callable, TypedDict

import celery
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
    server = crud.server.get(db, id=server_id)

    if server is None:
        raise RuntimeError(
            f"Can not find a server data with id {server_id} in a database"
        )

    def on_failed() -> None:
        assert server is not None
        crud.server.update(db, db_obj=server, obj_in={"status": "failed"})

    connection = console.ConnectionManager(server, self, db, on_failed=on_failed)

    with connection:
        root_content = connection.command.ls()
        if "chia-blockchain" not in root_content:
            connection.command.chia.install(cd="/root/")

        crud.server.update(db, db_obj=server, obj_in={"status": "connected"})

        return {"info": "done", "console": connection.console_logger.get()}
