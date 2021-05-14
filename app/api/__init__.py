from fastapi import APIRouter

from app.api.routes import user, login, tasks, server

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["Login"])
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(server.router, prefix="/server", tags=["Server"])
