from app.schemas import filtration
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


# @router.on_event("startup")
# @repeat_every(seconds=60, raise_exceptions=True)
# def scan_queues_on_servers() -> None:
#     db = DatabaseSession()
#     for plot_queue in crud.plot_queue.get_multi(db)[1]:
#         tasks.scan_plotting.delay(plot_queue.id)
#     db.close()


@cbv(router)
class TransferCBV(BaseAuthCBV):
    @router.post("/")
    def create_transfer(self, data: schemas.TransferCreate) -> schemas.TransferReturn:
        plot = crud.plot.get(self.db, id=data.plot_id)
        if plot is None:
            raise HTTPException(404, "Plot with such id is not found")
        if plot.status != schemas.PlotStatus.PLOTTED:
            raise HTTPException(403, "Can only transfer plotted plots")
        start_dir = plot.located_directory
        dest_dir = crud.directory.get(self.db, id=data.destination_directory_id)
        if dest_dir is None:
            raise HTTPException(404, "Directory with such id is not found")

        data_extended = schemas.TransferCreateExtended(
            **data.dict(), starting_directory_id=start_dir.id
        )
        transfer = crud.transfer.create(self.db, obj_in=data_extended)

        return schemas.TransferReturn.from_orm(transfer)

    @router.get("/")
    def get_transfers_table(
        self,
        filtration: schemas.FilterData[models.Transfer] = Depends(
            deps.get_filtration_data(models.Transfer)
        ),
    ) -> schemas.Table[schemas.TransferReturn]:
        amount, items = crud.transfer.get_multi(self.db, filtration=filtration)
        return schemas.Table[schemas.TransferReturn](amount=amount, items=items)
