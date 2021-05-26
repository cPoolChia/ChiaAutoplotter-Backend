from typing import Any, Callable, TypedDict

import celery
import time
from uuid import UUID
from app import schemas, crud
from app.core import console
from app.api import deps
from app.celery import celery as celery_app
from sqlalchemy.orm import Session
from app.db.session import DatabaseSession


@celery_app.task(bind=True)
def init_server_connect(
    self: celery.Task,
    server_id: UUID,
    *,
    db_factory: Callable[[], Session] = DatabaseSession,
) -> Any:
    db = db_factory()
    server = crud.server.get(db, id=server_id)
    directory_ids = [
        directory.id
        for directory in crud.directory.get_multi_by_server(db, server=server)[1]
    ]

    if server is None:
        raise RuntimeError(
            f"Can not find a server data with id {server_id} in a database"
        )

    def on_failed() -> None:
        assert server is not None
        crud.server.update(db, db_obj=server, obj_in={"status": "failed"})
        for directory_id in directory_ids:
            directory = crud.directory.get(db, id=directory_id)
            crud.directory.update(db, db_obj=directory, obj_in={"status": "pending"})

    connection = console.ConnectionManager(server, self, db, on_failed=on_failed)

    with connection:
        server = crud.server.update(db, db_obj=server, obj_in={"status": "connected"})
        if directory_ids != []:
            df = connection.command.df()
        for directory_id in directory_ids:
            directory = crud.directory.get(db, id=directory_id)
            try:
                connection.command.ls(dirname=directory.location)
            except NotADirectoryError:
                directory = crud.directory.update(
                    db, db_obj=directory, obj_in={"status": "failed"}
                )
            else:
                directory = crud.directory.update(
                    db, db_obj=directory, obj_in={"status": "monitoring"}
                )
                df = df.set_index("Mounted")
                indexes: list[str] = sorted(df.index, key=len, reverse=True)
                for index in indexes:
                    loc = directory.location
                    if loc.startswith(index) or loc.startswith("/root" + index):
                        used_memory = int(df.loc[index, "Used"]) * 1024
                        available_memory = int(df.loc[index, "Available"]) * 1024
                        directory = crud.directory.update(
                            db,
                            db_obj=directory,
                            obj_in={
                                "disk_size": available_memory,
                                "disk_taken": used_memory,
                            },
                        )
                        break
                else:
                    directory = crud.directory.update(
                        db, db_obj=directory, obj_in={"status": "failed"}
                    )

    if connection.failed_data is None:
        return {"info": "done", "console": connection.log_collector.get()}
    return connection.failed_data
