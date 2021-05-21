from app.core.console.log_collector import ConsoleLogCollector
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
    *,
    db_factory: Callable[[], Session] = lambda: next(deps.get_db()),
) -> Any:
    db = db_factory()
    log_collector = ConsoleLogCollector()
    for plot_queue in crud.plot_queue.get_multi(db)[1]:
        # Check how queue task is doing, and if it is failed, mark queue as failed
        task = celery_app.AsyncResult(str(plot_queue.id))
        if (
            task.status == "FAILURE"
            and plot_queue.status != schemas.PlotQueueStatus.FAILED.value
        ):
            crud.plot_queue.update(
                db,
                db_obj=plot_queue,
                obj_in={"status": schemas.PlotQueueStatus.FAILED.value},
            )

        connection = console.ConnectionManager(
            plot_queue.server, self, db, log_collector
        )

        with connection:
            # Check queue plot directory
            plot_location = f"{plot_queue.plot_dir}/{plot_queue.id}"
            plot_files = connection.command.ls(cd=plot_location)
            unique_plots = {
                ".".join(plot_file.split(".")[:2])
                for plot_file in plot_files
                if ".plot." in plot_file
            }
            for plot_name in unique_plots:
                plot = crud.plot.get_by_name(db, name=plot_name)
                if plot is None:
                    crud.plot.create(
                        db,
                        obj_in=schemas.PlotCreate(
                            name=plot_name,
                            location=plot_location,
                            created_queue_id=plot_queue.id,
                            located_server_id=plot_queue.server.id,
                            status=schemas.PlotStatus.PLOTTING,
                        ),
                    )

            # Check queue create directory
            created_location = f"{plot_queue.create_dir}/{plot_queue.id}"
            created_files = connection.command.ls(cd=created_location)
            for plot_name in created_files:
                plot = crud.plot.get_by_name(db, name=plot_name)
                if plot is None:
                    crud.plot.create(
                        db,
                        obj_in=schemas.PlotCreate(
                            name=plot_name,
                            location=plot_location,
                            created_queue_id=plot_queue.id,
                            located_server_id=plot_queue.server.id,
                            status=schemas.PlotStatus.PLOTTED,
                        ),
                    )
                elif plot.status != schemas.PlotStatus.PLOTTED.value:
                    crud.plot.update(
                        db,
                        db_obj=plot,
                        obj_in={"status": schemas.PlotStatus.PLOTTED.value},
                    )

    return {"info": "done", "console": connection.log_collector.get()}
