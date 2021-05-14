from typing import Any
from uuid import UUID

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import auth
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

router = InferringRouter()


@cbv(router)
class ServerCBV:
    user: models.User = Depends(deps.get_current_user)
    db: Session = Depends(deps.get_db)

    def get_server_by_id(
        server_id: UUID, db: Session = Depends(deps.get_db)
    ) -> models.Server:
        server = crud.server.get(db, server_id)
        if server is None:
            raise HTTPException(404, "Server with such id is not found")
        return server

    @router.get("/")
    def get_table(
        self,
        filtration: schemas.FilterData[models.Server] = Depends(
            deps.get_filtration_data(models.Server)
        ),
    ) -> schemas.Table[schemas.ServerReturn]:
        amount, items = crud.server.get_multi(self.db, filtration=filtration)

        return {
            "amount": amount,
            "items": [schemas.ServerReturn.from_orm(item) for item in items],
        }

    @router.get("/{server_id}/")
    def get_item(
        self, server: models.Server = Depends(get_server_by_id)
    ) -> schemas.ServerReturn:
        return schemas.ServerReturn.from_orm(server)

    @router.post("/")
    def add_item(
        self,
        data: schemas.ServerCreate,
    ) -> schemas.ServerReturn:
        server = crud.server.create(self.db, obj_in=data)
        return schemas.ServerReturn.from_orm(server)

    @router.put("/{server_id}/")
    def update_item(
        self,
        data: schemas.ServerUpdate,
        server: models.Server = Depends(get_server_by_id),
    ) -> schemas.ServerReturn:
        server = crud.server.update(self.db, db_obj=server, obj_in=data)
        return schemas.ServerReturn.from_orm(server)

    @router.delete("/{server_id}/")
    def delete_item(
        self, server: models.Server = Depends(get_server_by_id)
    ) -> schemas.Msg:
        crud.server.remove_obj(self.db, obj=server)
        return ""
