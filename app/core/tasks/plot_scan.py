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
from app.db.session import DatabaseSession, session_manager


@celery_app.task(bind=True)
def scan_plots_task(
    self: celery.Task,
    *,
    session_factory: Callable[[], Session] = DatabaseSession,
) -> Any:
    with session_manager(session_factory) as db:
        plot_queue_ids = [
            plot_queue.id for plot_queue in crud.plot_queue.get_multi(db)[1]
        ]
    log_collector = ConsoleLogCollector()

    for plot_queue_id in plot_queue_ids:
        with session_manager(session_factory) as db:
            plot_queue = crud.plot_queue.get(db, id=plot_queue_id)
            if plot_queue is None:
                raise ValueError(f"Can not find a plot queue with id {plot_queue_id}")

            plot_location = os.path.join(
                f"{plot_queue.temp_dir.location}", f"{plot_queue.id}"
            )
            created_location = os.path.join(
                f"{plot_queue.final_dir.location}", f"{plot_queue.id}"
            )
            server_data = schemas.ServerReturn.from_orm(plot_queue.server)

        connection = console.ConnectionManager(
            server_data, self, log_collector=log_collector
        )

        with connection:
            # Check queue plot directory
            unique_plots = {
                ".".join(plot_file.split(".")[:2])
                for plot_file in connection.command.ls(cd=plot_location)
                if ".plot." in plot_file
            }
            with session_manager(session_factory) as db:
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
            created_files = {
                plot
                for plot in connection.command.ls(cd=created_location)
                if plot.endswith(".plot")
            }
            with session_manager(session_factory) as db:
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
            with session_manager(session_factory) as db:
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

    return {"info": "done", "console": log_collector.get()}
