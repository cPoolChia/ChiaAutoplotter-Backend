from typing import Any
from uuid import UUID, uuid4
from . import plots, plot_queue
from datetime import datetime, timedelta
import celery

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import auth
from app.core import tasks
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from app.api.routes.base import BaseAuthCBV
from fastapi_utils.tasks import repeat_every
from app.db.session import DatabaseSession

router = InferringRouter()
router.include_router(plots.router, prefix="/{server_id}/plots", tags=["Plots"])
router.include_router(
    plot_queue.router, prefix="/{server_id}/queues", tags=["Plot Queue"]
)


@repeat_every(seconds=60)
@router.on_event("startup")
def scan_servers_connection() -> None:
    db = DatabaseSession()
    for server in crud.server.get_multi(db)[1]:
        tasks.init_server_connect.delay(server.id)


@cbv(router)
class ServerCBV(BaseAuthCBV):
    @router.get("/")
    def get_table(
        self,
        filtration: schemas.FilterData[models.Server] = Depends(
            deps.get_filtration_data(models.Server)
        ),
    ) -> schemas.Table[schemas.ServerReturn]:
        amount, items = crud.server.get_multi(self.db, filtration=filtration)
        return schemas.Table[schemas.ServerReturn](amount=amount, items=items)

    @router.get("/{server_id}/")
    def get_server(
        self, server: models.Server = Depends(deps.get_server_by_id)
    ) -> schemas.ServerReturn:
        return schemas.ServerReturn.from_orm(server)

    @router.post("/")
    def add_item(self, data: schemas.ServerCreate) -> schemas.ServerReturn:
        server = crud.server.create(self.db, obj_in=data)
        init_task: celery.AsyncResult = tasks.init_server_connect.apply_async(
            (server.id,), eta=datetime.now() + timedelta(seconds=5)
        )
        server = crud.server.update(
            self.db, db_obj=server, obj_in={"init_task_id": init_task.id}
        )

        return schemas.ServerReturn.from_orm(server)

    @router.put("/{server_id}/")
    def update_item(
        self,
        data: schemas.ServerUpdate,
        server: models.Server = Depends(deps.get_server_by_id),
    ) -> schemas.ServerReturn:
        if server.status == schemas.ServerStatus.CONNECTED.value:
            raise HTTPException(403, detail="Can not edit already connected server")

        server = crud.server.update(self.db, db_obj=server, obj_in=data)

        init_task: celery.AsyncResult = tasks.init_server_connect.apply_async(
            (server.id,), eta=datetime.now() + timedelta(seconds=15)
        )
        server.init_task_id = init_task.id

        server = crud.server.update(
            self.db, db_obj=server, obj_in={"init_task_id": init_task.id}
        )

        return schemas.ServerReturn.from_orm(server)

    @router.delete("/{server_id}/")
    def delete_item(
        self, server: models.Server = Depends(deps.get_server_by_id)
    ) -> schemas.Msg:
        try:
            crud.server.remove_obj(self.db, obj=server)
        except Exception as error:  # TODO
            raise HTTPException(
                403, detail="Server has connected entities, can not remove it"
            ) from error
        return {"msg": "Deleted"}
