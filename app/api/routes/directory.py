from app.schemas import filtration
from app.models import directory
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
    directory: models.Directory = Depends(deps.get_directory_by_id)

    @router.get("/{directory_id}/")
    def get_directory_data(self) -> schemas.DirectoryReturn:
        return schemas.DirectoryReturn.from_orm(self.directory)

    @router.get("/{directory_id}/plots/")
    def get_plots_in_directory(
        self,
        filtration: schemas.FilterData[models.Plot] = Depends(
            deps.get_filtration_data(models.Plot)
        ),
    ) -> schemas.Table[schemas.PlotReturn]:
        amount, items = crud.plot.get_multi_by_directory(
            self.db, directory=self.directory, filtration=filtration
        )
        return schemas.Table[schemas.PlotReturn](amount=amount, items=items)

    @router.get("/{directory_id}/queues/")
    def get_queues_linked_to_directory(
        self,
        filtration: schemas.FilterData[models.PlotQueue] = Depends(
            deps.get_filtration_data(models.PlotQueue)
        ),
    ) -> schemas.Table[schemas.PlotQueueReturn]:
        amount, items = crud.plot_queue.get_multi_linked_to_directory(
            self.db, directory=self.directory, filtration=filtration
        )
        return schemas.Table[schemas.PlotQueueReturn](amount=amount, items=items)

    @router.delete("/{directory_id}/")
    def remove_directory(self) -> schemas.Msg:
        linked_queues_amount, _ = crud.plot_queue.get_multi_linked_to_directory(
            self.db, directory=self.directory
        )

        if linked_queues_amount != 0 or len(self.directory.plots) != 0:
            raise HTTPException(
                403,
                detail="Can not remove directory because "
                "there are queues and/or plots, that use it",
            )
        crud.directory.remove_obj(self.db, obj=self.directory)
        return schemas.Msg(msg="Removed successfully")
