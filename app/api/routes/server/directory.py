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
class DirectoryCBV(BaseAuthCBV):
    server: models.Server = Depends(deps.get_server_by_id)

    @router.get("/")
    def get_directories_table(
        self,
        filtration: schemas.FilterData[models.Directory] = Depends(
            deps.get_filtration_data(models.Directory)
        ),
    ) -> schemas.Table[schemas.DirectoryReturn]:
        amount, items = crud.directory.get_multi_by_server(
            self.db, server=self.server, filtration=filtration
        )
        return schemas.Table[schemas.DirectoryReturn](amount=amount, items=items)

    @router.post("/")
    def add_new_dir(self, data: schemas.DirectoryCreate) -> schemas.DirectoryReturn:
        same_location = crud.directory.get_by_location_and_server(
            self.db, server=self.server
        )
        if same_location is not None:
            raise HTTPException(
                403, detail="This location already exists on this server"
            )
        new_dir = crud.directory.create(
            self.db,
            obj_in=schemas.DirectoryCreateExtended(
                **data.dict(), server_id=self.server.id
            ),
        )
        return schemas.DirectoryReturn.from_orm(new_dir)
