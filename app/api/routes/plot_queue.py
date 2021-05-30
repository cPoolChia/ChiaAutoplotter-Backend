from typing import Any
from uuid import UUID, uuid4
import celery

from datetime import datetime, timedelta
from app import crud, models, schemas
from app.celery import celery as celery_app
from app.api import deps
from app.core.config import settings
from app.utils import auth
from app.core import tasks
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.tasks import repeat_every
from app.api.routes.base import BaseAuthCBV
from app.db.session import DatabaseSession

router = InferringRouter()


@cbv(router)
class PlotQueueCBV(BaseAuthCBV):
    @router.post("/")
    def create_plot_queue(
        self, data: schemas.PlotQueueCreate
    ) -> schemas.PlotQueueReturn:
        server = crud.server.get(self.db, id=data.server_id)

        if server is None:
            raise HTTPException(404, detail="Server with such id is not found")

        temp_dir = crud.directory.get(self.db, id=data.temp_dir_id)
        final_dir = crud.directory.get(self.db, id=data.final_dir_id)
        if temp_dir is None:
            raise HTTPException(
                404, detail="Directory with such id is not found (Temporary directory)"
            )
        if final_dir is None:
            raise HTTPException(
                404, detail="Directory with such id is not found (Final directory)"
            )
        if temp_dir.server != server:
            raise HTTPException(
                403,
                detail="Directory's server id is different from serverId "
                "(Temporary directory)",
            )
        if final_dir.server != server:
            raise HTTPException(
                403,
                detail="Directory's server id is different from serverId "
                "(Final directory)",
            )

        plot_queue = crud.plot_queue.create(self.db, obj_in=data)
        plot_task = tasks.plot_queue_task.delay(plot_queue.id)
        plot_queue = crud.plot_queue.update(
            self.db, db_obj=plot_queue, obj_in={"plot_task_id": plot_task.id}
        )
        return schemas.PlotQueueReturn.from_orm(plot_queue)

    @router.post("/{plot_queue_id}/pause/")
    def pause_plot_queue(
        self, plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id)
    ) -> schemas.PlotQueueReturn:
        if plot_queue.plot_task_id is not None:
            task_result = celery_app.AsyncResult(str(plot_queue.plot_task_id))
            task_result.revoke(terminate=True)
        plot_queue = crud.plot_queue.update(
            self.db,
            db_obj=plot_queue,
            obj_in={"status": schemas.PlotQueueStatus.PAUSED.value},
        )
        return plot_queue

    @router.post("/{plot_queue_id}/restart/")
    def restart_plot_queue(
        self, plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id)
    ) -> schemas.PlotQueueReturn:
        if plot_queue.plot_task_id is None:
            raise HTTPException(
                409,
                detail="For some reason, task has no plot_task_id. "
                "If this error repeats, it might be a bug.",
            )

        task_result = celery_app.AsyncResult(str(plot_queue.plot_task_id))
        if (
            task_result.state not in ["FAILURE", "REVOKED"]
            and plot_queue.status != schemas.PlotQueueStatus.PAUSED.value
        ):
            raise HTTPException(
                403,
                detail="Task for this queue is not failed nor revoked, can not restart",
            )

        plot_task = tasks.plot_queue_task.delay(plot_queue.id)
        plot_queue = crud.plot_queue.update(
            self.db, db_obj=plot_queue, obj_in={"plot_task_id": plot_task.id}
        )
        return schemas.PlotQueueReturn.from_orm(plot_queue)

    @router.put("/{plot_queue_id}/")
    def update_plot_queue(
        self,
        data: schemas.PlotQueueUpdate,
        plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id),
    ) -> schemas.PlotQueueReturn:
        plot_queue = crud.plot_queue.update(self.db, db_obj=plot_queue, obj_in=data)
        return schemas.PlotQueueReturn.from_orm(plot_queue)

    @router.get("/")
    def get_queue_table(
        self,
        filtration: schemas.FilterData[models.PlotQueue] = Depends(
            deps.get_filtration_data(models.PlotQueue)
        ),
    ) -> schemas.Table[schemas.PlotQueueReturn]:
        amount, items = crud.plot_queue.get_multi(self.db, filtration=filtration)
        return schemas.Table[schemas.PlotQueueReturn](amount=amount, items=items)

    @router.get("/{plot_queue_id}/")
    def get_queue_data(
        self, plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id)
    ) -> schemas.PlotQueueReturn:
        return schemas.PlotQueueReturn.from_orm(plot_queue)

    @router.get("/{plot_queue_id}/plots/")
    def get_queue_plots_data(
        self,
        plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id),
        filtration: schemas.FilterData[models.PlotQueue] = Depends(
            deps.get_filtration_data(models.PlotQueue)
        ),
    ) -> schemas.Table[schemas.PlotReturn]:
        amount, items = crud.plot.get_multi_by_queue(
            self.db, queue=plot_queue, filtration=filtration
        )
        return schemas.Table[schemas.PlotReturn](amount=amount, items=items)
