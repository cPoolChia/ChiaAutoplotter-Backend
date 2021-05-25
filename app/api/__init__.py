from fastapi import APIRouter

from app.api.routes import (
    user,
    login,
    tasks,
    server,
    plot_queue,
    updates,
    directory,
    transfer,
)

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["Login"])
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(updates.router, prefix="/updates", tags=["Object Updates"])
api_router.include_router(server.router, prefix="/server", tags=["Server"])
api_router.include_router(plot_queue.router, prefix="/plot/queue", tags=["Plot Queue"])
api_router.include_router(
    directory.router, prefix="/directory/{directory_id}", tags=["Server Directory"]
)
api_router.include_router(transfer.router, prefix="/transfer", tags="Plot transfer")
