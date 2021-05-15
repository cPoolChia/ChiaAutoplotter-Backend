from typing import TypedDict, Any
from fastapi import APIRouter, WebSocket
from starlette.concurrency import run_in_threadpool
from app.celery import celery as celery_app
from app.core import tasks
from app import schemas

import asyncio

router = APIRouter()


@router.websocket_route("/ws/")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    task_id = websocket.query_params["uuid"]
    task = celery_app.AsyncResult(task_id)
    await websocket.send_json(task.get())

    state = celery_app.events.State()

    def callback(event: dict) -> None:
        state.event(event)
        if "uuid" in event and event["uuid"] == task_id:
            asyncio.run(websocket.send_json(schemas.TaskData(**event).dict()))

    with celery_app.connection() as connection:
        receiver = celery_app.events.Receiver(
            connection,
            handlers={
                "*": callback,
            },
        )
        await run_in_threadpool(receiver.capture, limit=None, timeout=None, wakeup=True)
