from app.core.console.log_collector import ConsoleLogCollector
from app.schemas.directory import DirectoryReturn
from typing import Any, Callable, TypedDict

import celery
import time
from uuid import UUID
from app import schemas, crud
from app.core import console
from app.api import deps
from app.celery import celery as celery_app
from sqlalchemy.orm import Session
from app.db.session import DatabaseSession, session_manager


@celery_app.task(bind=True)
def server_connect_task(
    self: celery.Task,
    *,
    session_factory: Callable[[], Session] = DatabaseSession,
) -> Any:
    with session_manager(session_factory) as db:
        server_ids = [server.id for server in crud.server.get_multi(db)[1]]
    log_collector = ConsoleLogCollector()

    for server_id in server_ids:
        with session_manager(session_factory) as db:
            server = crud.server.get(db, id=server_id)
            if server is None:
                raise RuntimeError(
                    f"Can not find a server data with id {server_id} in a database"
                )

            if server.init_task_id is not None:
                task = celery_app.AsyncResult(str(server.init_task_id))
                task.forget()

            server = crud.server.update(
                db, db_obj=server, obj_in={"init_task_id": self.request.id}
            )
            server_data = schemas.ServerReturn.from_orm(server)

            directory_objects = crud.directory.get_multi_by_server(db, server=server)[1]
            directories = [
                schemas.DirectoryReturn.from_orm(directory)
                for directory in directory_objects
            ]

        def on_failed() -> None:
            with session_manager(session_factory) as db:
                server = crud.server.get(db, id=server_id)
                if server is None:
                    return
                crud.server.update(db, db_obj=server, obj_in={"status": "failed"})
                for directory in directories:
                    directory_obj = crud.directory.get(db, id=directory.id)
                    if directory_obj is None:
                        continue
                    crud.directory.update(
                        db, db_obj=directory_obj, obj_in={"status": "failed"}
                    )

        connection = console.ConnectionManager(
            server_data, self, on_failed=on_failed, log_collector=log_collector
        )

        with connection:
            with session_manager(session_factory) as db:
                server = crud.server.get(db, id=server_id)
                if server is None:
                    raise RuntimeError(f"Server with id {server_id} has gone away")
                server = crud.server.update(
                    db, db_obj=server, obj_in={"status": "connected"}
                )
            for directory in directories:
                try:
                    filenames = connection.command.ls(dirname=directory.location)
                except NotADirectoryError:
                    with session_manager(session_factory) as db:
                        directory_obj = crud.directory.get(db, id=directory.id)
                        if directory_obj is not None:
                            directory_obj = crud.directory.update(
                                db, db_obj=directory_obj, obj_in={"status": "failed"}
                            )
                else:
                    df = connection.command.df(dirname=directory.location)
                    with session_manager(session_factory) as db:
                        directory_obj = crud.directory.get(db, id=directory.id)
                        directory_obj = crud.directory.update(
                            db, db_obj=directory_obj, obj_in={"status": "monitoring"}
                        )
                        standalone_plots = {
                            filename
                            for filename in filenames
                            if filename.endswith(".plot")
                        }
                        for plot_name in standalone_plots:
                            plot = crud.plot.get_by_name(db, name=plot_name)
                            if plot is None:
                                crud.plot.create(
                                    db,
                                    obj_in=schemas.PlotCreate(
                                        name=plot_name,
                                        created_queue_id=None,
                                        located_directory_id=directory.id,
                                        status=schemas.PlotStatus.PLOTTED,
                                    ),
                                )
                        total_used = sum(line["used"] for line in df)
                        total_size = sum(line["total"] for line in df)
                        directory_obj = crud.directory.update(
                            db,
                            db_obj=directory_obj,
                            obj_in={
                                "disk_size": total_size,
                                "disk_taken": total_used,
                            },
                        )

    return {"info": "done", "console": log_collector.get()}
