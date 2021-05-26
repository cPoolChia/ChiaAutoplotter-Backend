from app.core.console.log_collector import ConsoleLogCollector
from typing import Any, Callable, TypedDict

import celery
import os.path
import time
from datetime import datetime, timedelta
from uuid import UUID
from app import schemas, crud
from app.core import console
from app.api import deps
from app.celery import celery as celery_app
from sqlalchemy.orm import Session
from app.db.session import DatabaseSession


@celery_app.task(bind=True)
def scan_plotting(
    self: celery.Task,
    plot_queue_id: UUID,
    *,
    db_factory: Callable[[], Session] = DatabaseSession,
) -> Any:
    db = db_factory()
    log_collector = ConsoleLogCollector()
    plot_queue = crud.plot_queue.get(db, id=plot_queue_id)
    if plot_queue is None:
        raise ValueError(f"Can not find a plot queue with id {plot_queue_id}")

    connection = console.ConnectionManager(plot_queue.server, self, db, log_collector)

    # Check how queue task is doing, and if it is failed, mark queue as failed
    task = celery_app.AsyncResult(str(plot_queue.plot_task_id))
    if (
        task.status == "FAILURE"
        and plot_queue.status != schemas.PlotQueueStatus.FAILED.value
    ):
        plot_queue = crud.plot_queue.update(
            db,
            db_obj=plot_queue,
            obj_in={"status": schemas.PlotQueueStatus.FAILED.value},
        )

    with connection:
        # Check queue plot directory
        plot_location = os.path.join(
            f"{plot_queue.temp_dir.location}", f"/{plot_queue.id}"
        )
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
                        created_queue_id=plot_queue.id,
                        located_directory_id=plot_queue.temp_dir_id,
                        status=schemas.PlotStatus.PLOTTING,
                    ),
                )

        # Check queue create directory
        created_location = os.path.join(
            f"{plot_queue.final_dir.location}", f"/{plot_queue.id}"
        )
        created_files = {
            plot
            for plot in connection.command.ls(cd=created_location)
            if plot.endswith(".plot")
        }
        for plot_name in created_files:
            plot = crud.plot.get_by_name(db, name=plot_name)
            if plot is None:
                crud.plot.create(
                    db,
                    obj_in=schemas.PlotCreate(
                        name=plot_name,
                        created_queue_id=plot_queue.id,
                        located_directory_id=plot_queue.final_dir_id,
                        status=schemas.PlotStatus.PLOTTED,
                    ),
                )
            elif plot.status != schemas.PlotStatus.PLOTTED.value:
                plotting_duration = (
                    plot.created_queue.plotting_started - datetime.utcnow()
                    if plot.created_queue.plotting_started is not None
                    else None
                )
                crud.plot.update(
                    db,
                    db_obj=plot,
                    obj_in={
                        "status": schemas.PlotStatus.PLOTTED.value,
                        "located_directory_id": plot_queue.final_dir_id,
                        "plotting_duration": plotting_duration,
                    },
                )

        # If some plots were not found, mark them as lost
        found_plots = unique_plots | created_files
        queue_plots = crud.plot.get_multi_by_queue(db, queue=plot_queue)[1]
        for plot in queue_plots:
            if (
                plot.status
                in [
                    schemas.PlotStatus.PLOTTED.value,
                    schemas.PlotStatus.PLOTTING.value,
                    schemas.PlotStatus.PENDING.value,
                ]
                and plot.name not in found_plots
            ):
                crud.plot.update(
                    db,
                    db_obj=plot,
                    obj_in={"status": schemas.PlotStatus.LOST.value},
                )

    if connection.failed_data is None:
        return {"info": "done", "console": log_collector.get()}
    return connection.failed_data
