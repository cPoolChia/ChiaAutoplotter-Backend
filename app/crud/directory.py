from typing import Any, Optional
from app import schemas, models
from app.crud.base import CRUDBase
from sqlalchemy.orm import Session


class CRUDDirectory(
    CRUDBase[
        models.Directory,
        schemas.DirectoryCreateExtended,
        schemas.DirectoryUpdate,
        schemas.DirectoryReturn,
    ]
):
    def get_multi_by_server(
        self,
        db: Session,
        *,
        server: models.Server,
        filtration: schemas.FilterData[Any] = schemas.FilterData[Any]()
    ) -> tuple[int, list[models.Directory]]:
        query = db.query(self.model).filter(self.model.server == server)
        return self._filter_multi_query(query, filtration)

    def get_by_location_and_server(
        self, db: Session, *, server: models.Server, location: str
    ) -> Optional[models.Directory]:
        return (
            db.query(self.model)
            .filter(self.model.server == server, self.model.location == location)
            .first()
        )
