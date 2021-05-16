from typing import Any
from app import schemas, models
from app.crud.base import CRUDBase
from sqlalchemy.orm import Session


class CRUDPlot(CRUDBase[models.Plot, schemas.PlotCreate, schemas.PlotUpdate]):
    def get_multi_by_located_server(
        self,
        db: Session,
        *,
        server: models.Server,
        filtration: schemas.FilterData[Any] = schemas.FilterData[Any]()
    ) -> tuple[int, list[models.Plot]]:
        query = db.query(self.model).filter(self.model.located_server == server)
        return self._filter_multi_query(query, filtration)

    def get_multi_by_created_server(
        self,
        db: Session,
        *,
        server: models.Server,
        filtration: schemas.FilterData[Any] = schemas.FilterData[Any]()
    ) -> tuple[int, list[models.Plot]]:
        query = db.query(self.model).filter(self.model.created_server == server)
        return self._filter_multi_query(query, filtration)