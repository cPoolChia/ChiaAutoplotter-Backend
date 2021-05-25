from datetime import datetime, timedelta
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
from app.db.session import DatabaseSession


@celery_app.task(bind=True)
def plot_queue_task(
    self: celery.Task,
    plot_queue_id: UUID,
    *,
    db_factory: Callable[[], Session] = DatabaseSession,
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
        connection.command.rm(cd=plot_queue.plot_dir, dirname=f"{plot_queue.id}")
        connection.command.mkdir(cd="/root/", dirname=plot_dir)

        plot_queue = crud.plot_queue.update(
            db,
            db_obj=plot_queue,
            obj_in={"status": schemas.PlotQueueStatus.PLOTTING.value},
        )

        connection.command.chia.plots.create(
            cd="/root/chia-blockchain",
            create_dir=create_dir,
            plot_dir=plot_dir,
            pool_key=plot_queue.server.pool_key,
            farmer_key=plot_queue.server.farmer_key,
            plots_amount=plot_queue.plots_amount,
        )

        if plot_queue.autoplot:
            plot_task: celery.AsyncResult = plot_queue_task.apply_async(
                (plot_queue_id,), eta=datetime.now() + timedelta(seconds=15)
            )
            plot_queue = crud.plot_queue.update(
                db, db_obj=plot_queue, obj_in={"plot_task_id": plot_task.id}
            )
        else:
            plot_queue = crud.plot_queue.update(
                db,
                db_obj=plot_queue,
                obj_in={"status": schemas.PlotQueueStatus.PAUSED.value},
            )

        return {
            "info": "done",
            "console": connection.log_collector.get(),
            "next_task_id": plot_task.id,
        }
