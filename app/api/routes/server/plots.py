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
class PlotCBV(BaseAuthCBV):
    server: models.Server = Depends(deps.get_server_by_id)
    filtration: schemas.FilterData[models.Plot] = Depends(
        deps.get_filtration_data(models.Plot)
    )

    @router.get("/created/")
    def get_created_table(self) -> schemas.Table[schemas.PlotReturn]:
        amount, items = crud.plot.get_multi_by_created_server(
            self.db, server=self.server, filtration=self.filtration
        )
        return schemas.Table[schemas.PlotReturn](amount=amount, items=items)

    @router.get("/located/")
    def get_located_table(
        self,
    ) -> schemas.Table[schemas.PlotReturn]:
        amount, items = crud.plot.get_multi_by_located_server(
            self.db, server=self.server, filtration=self.filtration
        )
        return schemas.Table[schemas.PlotReturn](amount=amount, items=items)
