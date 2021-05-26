from typing import Any
from uuid import UUID, uuid4
from . import plots, plot_queue, directory
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
router.include_router(
    directory.router, prefix="/{server_id}/directory", tags=["Server Directory"]
)


@router.on_event("startup")
@repeat_every(seconds=60, raise_exceptions=True)
def scan_servers_connection() -> None:
    db = DatabaseSession()
    for server in crud.server.get_multi(db)[1]:
        tasks.init_server_connect.delay(server.id)
    db.close()


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

    @router.post("/", status_code=201)
    def add_item(self, data: schemas.ServerCreateExtended) -> schemas.ServerReturn:
        same_name_server = crud.server.get_by_name(self.db, name=data.name)
        if same_name_server is not None:
            raise HTTPException(403, detail="Server with such name already exists")

        same_hostname_server = crud.server.get_by_hostname(
            self.db, hostname=data.hostname
        )
        if same_hostname_server is not None:
            raise HTTPException(403, detail="Server with such hostname already exists")

        server = crud.server.create(self.db, obj_in=schemas.ServerCreate(**data.dict()))
        init_task: celery.AsyncResult = tasks.init_server_connect.apply_async(
            (server.id,), eta=datetime.now() + timedelta(seconds=5)
        )
        server = crud.server.update(
            self.db, db_obj=server, obj_in={"init_task_id": init_task.id}
        )
        server_id = server.id
        for directory in data.directories:
            crud.directory.create(
                self.db,
                obj_in=schemas.DirectoryCreateExtended(
                    location=directory, server_id=server_id
                ),
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
        amount, directories = crud.directory.get_multi_by_server(self.db, server=server)
        if amount != 0:
            raise HTTPException(
                403, detail="Can not remove server, as there are objects linked to it"
            )
        crud.server.remove_obj(self.db, obj=server)
        return {"msg": "Deleted"}
