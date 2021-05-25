from typing import Optional
from sqlalchemy.orm.session import Session
from app import schemas, models
from app.crud.base import CRUDBase


class CRUDTransfer(
    CRUDBase[
        models.Transfer,
        schemas.TransferCreateExtended,
        schemas.TransferUpdate,
        schemas.TransferReturn,
    ]
):
    ...