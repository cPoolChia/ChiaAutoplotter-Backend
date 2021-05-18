from typing import Any, Callable, TypedDict

import celery
import time
from datetime import datetime, timedelta
from uuid import UUID
from app import schemas, crud
from app.core import console
from app.api import deps
from app.celery import celery as celery_app
from sqlalchemy.orm import Session


@celery_app.task(bind=True)
def scan_plotting(
    self: celery.Task,
    plot_queue_id: UUID,
    *,
    db_factory: Callable[[], Session] = lambda: next(deps.get_db()),
) -> Any:
    db = db_factory()
    console_logger = console.ConsoleLogCollector()
    plot_queue = crud.plot_queue.get(db, id=plot_queue_id)

    if plot_queue is None:
        raise RuntimeError(
            f"Can not find a plot queue with id {plot_queue_id} in a database"
        )

    connection = console.ConnectionManager(plot_queue.server, self, console_logger, db)

    with connection:
        plot_location = f"{plot_queue.plot_dir}/{plot_queue.id}"
        plotting_files = connection.command.ls(cd=plot_location)
        unique_plots = {
            ".".join(plotting_file.split(".")[:2])
            for plotting_file in plotting_files
            if ".plot." in plotting_file
        }
        for plot_name in unique_plots:
            plot = crud.plot.get_by_name(db, name=plot_name)
            if plot is None:
                crud.plot.create(
                    db,
                    obj_in=schemas.PlotCreate(
                        name=plot_name,
                        location=plot_location,
                        created_server_id=plot_queue.server.id,
                        located_server_id=plot_queue.server.id,
                        status=schemas.PlotStatus.PLOTTING,
                    ),
                )

    scan_task: celery.AsyncResult = scan_plotting.apply_async(
        (plot_queue_id,), eta=datetime.now() + timedelta(seconds=15)
    )

    return {"info": "done", "console": console_logger.get()}
