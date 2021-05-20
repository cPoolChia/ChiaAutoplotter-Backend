from app import schemas
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.celery import celery as celery_app
from app.api import deps
from app.core import listeners

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
    await websocket.send_json({"connected": "true"})
    task = celery_app.AsyncResult(str(uuid))
    task_data = jsonable_encoder(
        schemas.TaskData(
            uuid=str(uuid),
            state="FINISHED",
            timestamp=time.time(),
            result=task.info,
            data={},
        )
    )
    if task.ready():
        await websocket.send_json(task_data)
    else:
        if task.info != None:
            await websocket.send_json(task_data | {"state": "PENDING"})
        connection_id = celery_events_listener.connect(websocket, uuid)

        try:
            while True:
                await websocket.receive_json()
        except WebSocketDisconnect:
            celery_events_listener.disconnect(connection_id)
