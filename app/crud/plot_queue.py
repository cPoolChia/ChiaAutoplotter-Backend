from typing import Any
from app import schemas, models
from app.crud.base import CRUDBase
from sqlalchemy.orm import Session


class CRUDPlotQueue(
    CRUDBase[models.PlotQueue, schemas.PlotQueueCreate, schemas.PlotQueueUpdate]
):
    ...