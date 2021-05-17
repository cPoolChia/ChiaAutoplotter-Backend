from typing import Any
from uuid import UUID, uuid4
import celery

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import auth
from app.core import tasks
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

router = InferringRouter()


@cbv(router)
class PlotQueueCBV:
    # user: models.User = Depends(deps.get_current_user)
    db: Session = Depends(deps.get_db)

    @router.post("/")
    def create_plot_queue(
        self, data: schemas.PlotQueueCreate
    ) -> schemas.PlotQueueReturn:
        plot_queue_id = uuid4()
        plot_queue = crud.plot_queue.create(self.db, obj_in=data)
        plot_task: celery.AsyncResult = tasks.plot_queue_task.delay(plot_queue_id)
        plot_queue.plot_task_id = plot_task.id
        plot_queue.id = plot_queue_id

        self.db.add(plot_queue)
        self.db.commit()
        self.db.refresh(plot_queue)
        return schemas.PlotQueueReturn.from_orm(plot_queue)
