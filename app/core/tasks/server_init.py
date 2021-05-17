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
    console_logger = console.ConsoleLogCollector()
    server = crud.server.get(db, id=server_id)
    connection = console.ConnectionManager(server, self, console_logger, db)

    if server is None:
        raise RuntimeError(
            f"Can not find a server data with id {server_id} in a database"
        )

    with connection:
        root_content = connection.command.ls()
        if "chia-blockchain" not in root_content:
            connection.command.chia.install(cd="/root/")

        if "plots" in root_content:
            # If there are already some plots on server on startup,
            # list them and add them to db
            plot_files = connection.command.ls(cd="/root/plots")
            plots_plotting = {
                plot_name.split(".")[0]
                for plot_name in plot_files
                if ".plot." in plot_name
            }
            plots_finished = {
                plot_name.split(".")[0]
                for plot_name in plot_files
                if plot_name.endswith(".plot")
            }

            for plot_name in plots_plotting:
                crud.plot.create(
                    db,
                    obj_in=schemas.PlotCreate(
                        name=plot_name,
                        created_server_id=server.id,
                        located_server_id=server.id,
                        status=schemas.PlotStatus.PLOTTING,
                    ),
                )

            for plot_name in plots_finished:
                crud.plot.create(
                    db,
                    obj_in=schemas.PlotCreate(
                        name=plot_name,
                        created_server_id=server.id,
                        located_server_id=server.id,
                        status=schemas.PlotStatus.PLOTTED,
                    ),
                )

    crud.server.update(db, db_obj=server, obj_in={"status": "connected"})

    return {"info": "done", "console": console_logger.get()}
