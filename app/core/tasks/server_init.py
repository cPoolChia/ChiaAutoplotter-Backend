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
    server = crud.server.update(
        db, db_obj=server, obj_in={"init_task_id": self.request.id}
    )
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
            crud.directory.update(db, db_obj=directory, obj_in={"status": "failed"})

    connection = console.ConnectionManager(server, self, db, on_failed=on_failed)

    with connection:
        server = crud.server.update(db, db_obj=server, obj_in={"status": "connected"})
        for directory_id in directory_ids:
            directory = crud.directory.get(db, id=directory_id)
            try:
                filenames = connection.command.ls(dirname=directory.location)
            except NotADirectoryError:
                directory = crud.directory.update(
                    db, db_obj=directory, obj_in={"status": "failed"}
                )
            else:
                directory = crud.directory.update(
                    db, db_obj=directory, obj_in={"status": "monitoring"}
                )
                standalone_plots = {
                    filename for filename in filenames if filename.endswith(".plot")
                }
                for plot_name in standalone_plots:
                    plot = crud.plot.get_by_name(db, name=plot_name)
                    if plot is None:
                        crud.plot.create(
                            db,
                            obj_in=schemas.PlotCreate(
                                name=plot_name,
                                created_queue_id=None,
                                located_directory_id=directory_id,
                                status=schemas.PlotStatus.PLOTTED,
                            ),
                        )
                directory = crud.directory.get(db, id=directory_id)
                df = connection.command.df(dirname=directory.location)
                total_used = sum(line["used"] for line in df)
                total_size = sum(line["total"] for line in df)
                directory = crud.directory.update(
                    db,
                    db_obj=directory,
                    obj_in={
                        "disk_size": total_size,
                        "disk_taken": total_used,
                    },
                )

    if connection.failed_data is None:
        return {"info": "done", "console": connection.log_collector.get()}
    return connection.failed_data
