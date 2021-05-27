from app import schemas
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.celery import celery as celery_app
from app.api import deps
from app.core import listeners
from app.core.console import ConnectionManager

from uuid import UUID
import time
from fastapi.encoders import jsonable_encoder
import asyncio

router = APIRouter()


@router.websocket("/ws/")
async def websocket_endpoint(
    websocket: WebSocket,
    uuid: UUID,
    # user: models.User = Depends(deps.get_current_user),
    celery_events_listener: listeners.TaskEventsListener = Depends(
        deps.get_events_listener
    ),
) -> None:
    await websocket.accept()
    task = celery_app.AsyncResult(str(uuid))
    task_data = jsonable_encoder(
        schemas.TaskData(
            uuid=str(uuid),
            state=task.state,
            timestamp=time.time(),
            data=task.info,
        ),
        custom_encoder={
            ConnectionManager.TaskRuntimeError: lambda e: {
                "console": e.args[0],
                "type": e.args[1],
                "error": e.args[2],
            }
        },
    )
    await websocket.send_json(task_data)

    if not task.ready():
        connection_id = celery_events_listener.connect(websocket, uuid)
        try:
            while True:
                await websocket.receive_json()
        except WebSocketDisconnect:
            celery_events_listener.disconnect(connection_id)
