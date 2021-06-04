from uuid import UUID
from app import crud, models, schemas
from app.celery import celery as celery_app
from app.api import deps
from app.core import listeners, tasks
from fastapi import Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi.encoders import jsonable_encoder
from app.api.routes.base import BaseAuthCBV
from app.db.session import DatabaseSession, session_manager
import time
import websockets

router = InferringRouter()


@cbv(router)
class PlotQueueCBV(BaseAuthCBV):
    @router.post("/")
    def create_plot_queue(
        self, data: schemas.PlotQueueCreate
    ) -> schemas.PlotQueueReturn:
        server = crud.server.get(self.db, id=data.server_id)

        if server is None:
            raise HTTPException(404, detail="Server with such id is not found")

        temp_dir = crud.directory.get(self.db, id=data.temp_dir_id)
        final_dir = crud.directory.get(self.db, id=data.final_dir_id)
        if temp_dir is None:
            raise HTTPException(
                404, detail="Directory with such id is not found (Temporary directory)"
            )
        if final_dir is None:
            raise HTTPException(
                404, detail="Directory with such id is not found (Final directory)"
            )
        if temp_dir.server != server:
            raise HTTPException(
                403,
                detail="Directory's server id is different from serverId "
                "(Temporary directory)",
            )
        if final_dir.server != server:
            raise HTTPException(
                403,
                detail="Directory's server id is different from serverId "
                "(Final directory)",
            )

        plot_queue = crud.plot_queue.create(self.db, obj_in=data)
        return schemas.PlotQueueReturn.from_orm(plot_queue)

    @router.post("/{plot_queue_id}/pause/")
    def pause_plot_queue(
        self, plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id)
    ) -> schemas.PlotQueueReturn:
        # TODO
        return plot_queue

    @router.post("/{plot_queue_id}/restart/")
    def restart_plot_queue(
        self, plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id)
    ) -> schemas.PlotQueueReturn:
        if plot_queue.status != schemas.PlotQueueStatus.FAILED.value:
            raise HTTPException(403, detail="Plot queue is not failed to restart.")

        plot_queue = crud.plot_queue.update(
            self.db,
            db_obj=plot_queue,
            obj_in={
                "execution_id": None,
                "status": schemas.PlotQueueStatus.PENDING.value,
            },
        )
        return schemas.PlotQueueReturn.from_orm(plot_queue)

    @router.put("/{plot_queue_id}/")
    def update_plot_queue(
        self,
        data: schemas.PlotQueueUpdate,
        plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id),
    ) -> schemas.PlotQueueReturn:
        plot_queue = crud.plot_queue.update(self.db, db_obj=plot_queue, obj_in=data)
        return schemas.PlotQueueReturn.from_orm(plot_queue)

    @router.get("/")
    def get_queue_table(
        self,
        filtration: schemas.FilterData[models.PlotQueue] = Depends(
            deps.get_filtration_data(models.PlotQueue)
        ),
    ) -> schemas.Table[schemas.PlotQueueReturn]:
        amount, items = crud.plot_queue.get_multi(self.db, filtration=filtration)
        return schemas.Table[schemas.PlotQueueReturn](amount=amount, items=items)

    @router.get("/{plot_queue_id}/")
    def get_queue_data(
        self, plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id)
    ) -> schemas.PlotQueueReturn:
        return schemas.PlotQueueReturn.from_orm(plot_queue)

    @router.get("/{plot_queue_id}/plots/")
    def get_queue_plots_data(
        self,
        plot_queue: models.PlotQueue = Depends(deps.get_plot_queue_by_id),
        filtration: schemas.FilterData[models.PlotQueue] = Depends(
            deps.get_filtration_data(models.PlotQueue)
        ),
    ) -> schemas.Table[schemas.PlotReturn]:
        amount, items = crud.plot.get_multi_by_queue(
            self.db, queue=plot_queue, filtration=filtration
        )
        return schemas.Table[schemas.PlotReturn](amount=amount, items=items)


@router.websocket("/ws/")
async def websocket_endpoint(
    websocket: WebSocket,
    uuid: UUID,
    # user: models.User = Depends(deps.get_current_user),
) -> None:
    await websocket.accept()
    with session_manager(DatabaseSession) as db:
        plot_queue = crud.plot_queue.get(db, id=uuid)
        if plot_queue is None:
            return await websocket.send_json({"error": "No plot queue with such id"})

        if plot_queue.execution_id is None:
            return await websocket.send_json(
                {"error": "No execution is bound to a queue"}
            )

        host = plot_queue.server.hostname.split(":")[0]
        port = plot_queue.server.worker_port
        uri = (
            f"ws://{host}:{port}/plotting/ws/"
            f"?execution_id={plot_queue.execution_id}"
        )

    async with websockets.connect(uri) as proxy_websocket:
        while True:
            data = await proxy_websocket.recv()
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            await websocket.send_text(data)
