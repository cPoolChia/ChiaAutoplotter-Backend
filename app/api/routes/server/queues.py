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
from app.api.routes.base import BaseAuthCBV

router = InferringRouter()


@cbv(router)
class QueueCBV(BaseAuthCBV):
    @router.get("/")
    def get_queues_table(
        self,
        server: models.Server = Depends(deps.get_server_by_id),
        filtration: schemas.FilterData[models.Plot] = Depends(
            deps.get_filtration_data(models.Plot)
        ),
    ) -> schemas.Table[schemas.PlotQueueReturn]:
        amount, items = crud.plot_queue.get_multi_by_server(
            self.db, server=server, filtration=filtration
        )
        return schemas.Table[schemas.PlotQueueReturn](amount=amount, items=items)