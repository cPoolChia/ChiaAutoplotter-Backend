from typing import Any
from uuid import UUID, uuid4
import celery

from datetime import datetime, timedelta
from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import auth
from app.core import tasks
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from app.api.routes.base import BaseAuthCBV

router = InferringRouter()


@cbv(router)
class PlotQueueCBV(BaseAuthCBV):
    @router.post("/")
    def create_plot_queue(
        self, data: schemas.PlotQueueCreate
    ) -> schemas.PlotQueueReturn:
        plot_queue = crud.plot_queue.create(self.db, obj_in=data)

        plot_task = tasks.plot_queue_task.delay(plot_queue.id)
        scan_task: celery.AsyncResult = tasks.scan_plotting.apply_async(
            (plot_queue.id,), eta=datetime.now() + timedelta(seconds=15)
        )

        crud.plot_queue.update(self.db, db_obj=plot_queue, obj_in={"plot_task_id": plot_task.id})
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
