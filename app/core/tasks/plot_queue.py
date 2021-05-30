from app.core.console.log_collector import ConsoleLogCollector
from datetime import datetime, timedelta
from typing import Any, Callable, TypedDict

import celery
import time
import os.path
from uuid import UUID

from sqlalchemy.sql import schema
from app import models, schemas, crud
from app.core import console
from app.api import deps
from app.celery import celery as celery_app
from sqlalchemy.orm import Session
from app.db.session import DatabaseSession, session_manager


@celery_app.task(bind=True)
def plot_queue_task(
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
                raise RuntimeError(
                    f"Can not find a plot queue with id {plot_queue_id} in a database"
                )

            if plot_queue.plot_task_id is not None:
                task = celery_app.AsyncResult(str(plot_queue.plot_task_id))
                task.forget()

            plot_queue = crud.plot_queue.update(
                db,
                db_obj=plot_queue,
                obj_in={
                    "status": schemas.PlotQueueStatus.PLOTTING.value,
                    "plotting_started": datetime.utcnow(),
                    "plot_task_id": self.request.id,
                },
            )
            server_data = schemas.ServerReturn.from_orm(plot_queue.server)
            final_dir = plot_queue.final_dir.location
            final_dir_sub = os.path.join(final_dir, f"{plot_queue.id}")
            temp_dir = plot_queue.temp_dir.location
            temp_dir_sub = os.path.join(temp_dir, f"{plot_queue.id}")
            pool_key = plot_queue.server.pool_key
            farmer_key = plot_queue.server.farmer_key
            plots_amount = plot_queue.plots_amount

        def on_failed() -> None:
            with session_manager(session_factory) as db:
                plot_queue = crud.plot_queue.get(db, id=plot_queue_id)
                if plot_queue is None:
                    return
                crud.plot_queue.update(
                    db,
                    db_obj=plot_queue,
                    obj_in={"status": schemas.PlotQueueStatus.FAILED.value},
                )

        def on_success() -> None:
            with session_manager(session_factory) as db:
                plot_queue = crud.plot_queue.get(db, id=plot_queue_id)
                if plot_queue is None:
                    return
                crud.plot_queue.update(
                    db,
                    db_obj=plot_queue,
                    obj_in={"status": schemas.PlotQueueStatus.WAITING.value},
                )

        connection = console.ConnectionManager(
            server_data,
            self,
            on_failed=on_failed,
            on_success=on_success,
            log_collector=log_collector,
        )

        with connection:
            root_content = connection.command.ls()
            if "chia-blockchain" not in root_content:
                connection.command.chia.install(cd="/root/")
            connection.command.chia.init(cd="/root/chia-blockchain")

            connection.command.mkdir(dirname=final_dir_sub)
            connection.command.rm(cd=temp_dir, dirname=f"{plot_queue_id}")
            connection.command.mkdir(dirname=temp_dir_sub)

            connection.command.chia.plots.create(
                cd="/root/chia-blockchain",
                create_dir=final_dir_sub,
                plot_dir=temp_dir_sub,
                pool_key=pool_key,
                farmer_key=farmer_key,
                plots_amount=plots_amount,
            )

    return {"info": "done", "console": log_collector.get()}
