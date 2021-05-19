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
def plot_queue_task(
    self: celery.Task,
    plot_queue_id: UUID,
    *,
    db_factory: Callable[[], Session] = lambda: next(deps.get_db()),
) -> Any:
    db = db_factory()
    plot_queue = crud.plot_queue.get(db, id=plot_queue_id)

    if plot_queue is None:
        raise RuntimeError(
            f"Can not find a plot queue with id {plot_queue_id} in a database"
        )

    connection = console.ConnectionManager(plot_queue.server, self, db)

    with connection:
        root_content = connection.command.ls()
        if "chia-blockchain" not in root_content:
            connection.command.chia.install(cd="/root/")

        connection.command.chia.init(cd="/root/chia-blockchain")

        create_dir = plot_queue.create_dir + f"/{plot_queue.id}"
        plot_dir = plot_queue.plot_dir + f"/{plot_queue.id}"

        connection.command.mkdir(cd="/root/", dirname=create_dir)
        connection.command.mkdir(cd="/root/", dirname=plot_dir)

        connection.command.chia.plots.create(
            cd="/root/chia-blockchain",
            create_dir=create_dir,
            plot_dir=plot_dir,
            pool_key=plot_queue.pool_key,
            farmer_key=plot_queue.farmer_key,
            plots_amount=plot_queue.plots_amount,
        )

        plots = connection.command.ls(cd=plot_dir)
        for plot_name in plots:
            plot = crud.plot.get_by_name(db, name=plot_name)
            if plot is None:
                crud.plot.create(
                    db,
                    obj_in=schemas.PlotCreate(
                        name=plot_name,
                        location=create_dir,
                        created_queue_id=plot_queue.id,
                        located_server_id=plot_queue.server.id,
                        status=schemas.PlotStatus.PLOTTING,
                    ),
                )
            else:
                crud.plot.update(
                    db, db_obj=plot, obj_in={"status": schemas.PlotStatus.PLOTTED}
                )

        plot_task: celery.AsyncResult = plot_queue_task.delay(plot_queue_id)
        plot_queue = crud.plot_queue.update(
            db, db_obj=plot_queue, obj_in={"plot_task_id": plot_task.id}
        )

        return {
            "info": "done",
            "console": connection.console_logger.get(),
            "next_task_id": plot_task.id,
        }
