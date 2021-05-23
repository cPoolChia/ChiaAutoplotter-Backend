from typing import Any
from app import schemas, models
from app.crud.base import CRUDBase
from sqlalchemy.orm import Session


class CRUDPlotQueue(
    CRUDBase[
        models.PlotQueue,
        schemas.PlotQueueCreate,
        schemas.PlotQueueUpdate,
        schemas.PlotQueueReturn,
    ]
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

    def get_multi_linked_to_directory(
        self,
        db: Session,
        *,
        directory: models.Directory,
        filtration: schemas.FilterData[Any] = schemas.FilterData[Any]()
    ) -> tuple[int, list[models.PlotQueue]]:
        query = db.query(self.model).filter(
            (self.model.temp_dir == directory) | (self.model.final_dir == directory)
        )
        return self._filter_multi_query(query, filtration)
