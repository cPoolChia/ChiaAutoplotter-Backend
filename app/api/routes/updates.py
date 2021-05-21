from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.api import deps
from app.core import listeners

from uuid import UUID
import asyncio
import warnings

router = APIRouter()


@router.websocket("/ws/")
async def websocket_endpoint(
    websocket: WebSocket,
    object_update_listener: listeners.ObjectUpdateListener = Depends(
        deps.get_object_update_listener
    ),
) -> None:
    await websocket.accept()
    connection_id = object_update_listener.connect(websocket)
    await websocket.send_json({"connected": True})

    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        object_update_listener.disconnect(connection_id)
