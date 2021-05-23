from typing import Optional
from sqlalchemy.orm.session import Session
from app import schemas, models
from app.crud.base import CRUDBase


class CRUDServer(
    CRUDBase[
        models.Server, schemas.ServerCreate, schemas.ServerUpdate, schemas.ServerReturn
    ]
):
    def get_by_name(self, db: Session, *, name: str) -> Optional[models.Server]:
        return db.query(self.model).filter(self.model.name == name).first()

    def get_by_hostname(self, db: Session, *, hostname: str) -> Optional[models.Server]:
        return db.query(self.model).filter(self.model.hostname == hostname).first()