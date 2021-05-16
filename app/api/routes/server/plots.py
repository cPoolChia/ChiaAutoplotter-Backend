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
class PlotCBV:
    # user: models.User = Depends(deps.get_current_user)
    db: Session = Depends(deps.get_db)

    @router.get("/created/")
    def get_created_table(
        self,
        server: models.Server = Depends(deps.get_server_by_id),
        filtration: schemas.FilterData[models.Plot] = Depends(
            deps.get_filtration_data(models.Plot)
        ),
    ) -> schemas.Table[schemas.PlotReturn]:
        amount, items = crud.plot.get_multi_by_created_server(
            self.db, server=server, filtration=filtration
        )
        return schemas.Table[schemas.PlotReturn](amount=amount, items=items)

    @router.get("/located/")
    def get_located_table(
        self,
        server: models.Server = Depends(deps.get_server_by_id),
        filtration: schemas.FilterData[models.Plot] = Depends(
            deps.get_filtration_data(models.Plot)
        ),
    ) -> schemas.Table[schemas.PlotReturn]:
        amount, items = crud.plot.get_multi_by_located_server(
            self.db, server=server, filtration=filtration
        )
        return schemas.Table[schemas.PlotReturn](amount=amount, items=items)
