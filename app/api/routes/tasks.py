from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.celery import celery as celery_app
from app.api import deps
from app.core import listeners

from uuid import UUID
import asyncio

router = APIRouter()


@router.websocket("/ws/")
async def websocket_endpoint(
    websocket: WebSocket,
    celery_events_listener: listeners.TaskEventsListener = Depends(
        deps.get_events_listener
    ),
) -> None:
    await websocket.accept()
    await websocket.send_json({"connected": "true"})

    task_id = websocket.query_params["uuid"]
    task = celery_app.AsyncResult(task_id)
    if task.ready():
        await websocket.send_json(task.get())
    else:
        if task.info != None:
            await websocket.send_json(task.info)
        connection_id = celery_events_listener.connect(websocket, UUID(task_id))

        try:
            while True:
                await websocket.receive_json()
        except WebSocketDisconnect:
            celery_events_listener.disconnect(connection_id)
