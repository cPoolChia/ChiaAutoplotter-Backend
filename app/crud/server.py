from app import schemas, models
from app.crud.base import CRUDBase


class CRUDServer(
    CRUDBase[
        models.Server, schemas.ServerCreate, schemas.ServerUpdate, schemas.ServerReturn
    ]
):
    ...