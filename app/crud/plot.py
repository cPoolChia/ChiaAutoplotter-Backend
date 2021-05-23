from typing import Any, Optional
from app import schemas, models
from app.crud.base import CRUDBase
from sqlalchemy.orm import Session


class CRUDPlot(
    CRUDBase[models.Plot, schemas.PlotCreate, schemas.PlotUpdate, schemas.PlotReturn]
):
    def get_by_name(self, db: Session, *, name: str) -> Optional[models.Plot]:
        return db.query(self.model).filter(self.model.name == name).first()

    def get_multi_by_located_server(
        self,
        db: Session,
        *,
        server: models.Server,
        filtration: schemas.FilterData[Any] = schemas.FilterData[Any]()
    ) -> tuple[int, list[models.Plot]]:
        query = (
            db.query(self.model)
            .join(models.Directory)
            .filter(models.Directory.server == server)
        )
        return self._filter_multi_query(query, filtration)

    def get_multi_by_created_server(
        self,
        db: Session,
        *,
        server: models.Server,
        filtration: schemas.FilterData[Any] = schemas.FilterData[Any]()
    ) -> tuple[int, list[models.Plot]]:
        query = (
            db.query(self.model)
            .join(models.PlotQueue)
            .filter(models.PlotQueue.server == server)
        )
        return self._filter_multi_query(query, filtration)

    def get_multi_by_directory(
        self,
        db: Session,
        *,
        directory: models.Directory,
        filtration: schemas.FilterData[Any] = schemas.FilterData[Any]()
    ) -> tuple[int, list[models.Plot]]:
        query = db.query(self.model).filter(self.model.located_directory == directory)
        return self._filter_multi_query(query, filtration)

    def get_multi_by_queue(
        self,
        db: Session,
        *,
        queue: models.PlotQueue,
        filtration: schemas.FilterData[Any] = schemas.FilterData[Any]()
    ) -> tuple[int, list[models.Plot]]:
        query = db.query(self.model).filter(self.model.created_queue == queue)
        return self._filter_multi_query(query, filtration)