from typing import Any, Callable, TypedDict

import celery
import time
from uuid import UUID

from sqlalchemy.sql import schema
from app import models, schemas, crud
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

    def on_failed() -> None:
        assert plot_queue is not None
        crud.plot_queue.update(
            db,
            db_obj=plot_queue,
            obj_in={"status": schemas.PlotQueueStatus.FAILED.value},
        )

    def on_success() -> None:
        assert plot_queue is not None
        crud.plot_queue.update(
            db,
            db_obj=plot_queue,
            obj_in={"status": schemas.PlotQueueStatus.WAITING.value},
        )

    connection = console.ConnectionManager(
        plot_queue.server, self, db, on_failed=on_failed, on_success=on_success
    )

    with connection:
        root_content = connection.command.ls()
        if "chia-blockchain" not in root_content:
            connection.command.chia.install(cd="/root/")

        connection.command.chia.init(cd="/root/chia-blockchain")

        create_dir = plot_queue.create_dir + f"/{plot_queue.id}"
        plot_dir = plot_queue.plot_dir + f"/{plot_queue.id}"

        connection.command.mkdir(cd="/root/", dirname=create_dir)
        connection.command.mkdir(cd="/root/", dirname=plot_dir)

        crud.plot_queue.update(
            db,
            db_obj=plot_queue,
            obj_in={"status": schemas.PlotQueueStatus.PLOTTING.value},
        )

        connection.command.chia.plots.create(
            cd="/root/chia-blockchain",
            create_dir=create_dir,
            plot_dir=plot_dir,
            pool_key=plot_queue.pool_key,
            farmer_key=plot_queue.farmer_key,
            plots_amount=plot_queue.plots_amount,
        )

        plot_task: celery.AsyncResult = plot_queue_task.delay(plot_queue_id)
        plot_queue = crud.plot_queue.update(
            db, db_obj=plot_queue, obj_in={"plot_task_id": plot_task.id}
        )

        return {
            "info": "done",
            "console": connection.log_collector.get(),
            "next_task_id": plot_task.id,
        }
