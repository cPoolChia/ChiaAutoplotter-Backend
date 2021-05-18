from typing import Any
from app import schemas, models
from app.crud.base import CRUDBase
from sqlalchemy.orm import Session


class CRUDPlotQueue(
    CRUDBase[models.PlotQueue, schemas.PlotQueueCreate, schemas.PlotQueueUpdate]
):
    def get_multi_by_server(
        self,
        db: Session,
        *,
        server: models.Server,
        filtration: schemas.FilterData[Any] = schemas.FilterData[Any]()
    ) -> tuple[int, list[models.PlotQueue]]:
        query = db.query(self.model).filter(self.model.server == server)
        return self._filter_multi_query(query, filtration)