from datetime import timedelta, datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.db.session import DatabaseSession
from app.db import init_db
from app.core.config import settings
from app.core import listeners, tasks
from app.api import deps
from app import crud, schemas
from fastapi.logger import logger


app = FastAPI(
    title=f"{settings.PROJECT_NAME} Rest API",
    description=f"An API for {settings.PROJECT_NAME}",
    version="0.2.1",
    openapi_tags=[
        {
            "name": "Login",
            "description": "Operations related to login.",
        },
        {
            "name": "User",
            "description": "Operations related to user account.",
        },
        {
            "name": "Plots",
            "description": "Operations related to plots.",
        },
        {
            "name": "Plot Queue",
            "description": "Operations related to plot queues.",
        },
        {
            "name": "Server",
            "description": "Operations related to servers.",
        },
    ],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def startup_event() -> None:
    session = DatabaseSession()
    try:
        if not settings.SKIP_DB_INIT:
            init_db(session)
        else:
            logger.info("Skipped database init (settings.SKIP_DB_INIT == True)")

        for server in crud.server.get_multi(session)[1]:
            crud.server.update(
                session,
                db_obj=server,
                obj_in={"status": schemas.ServerStatus.PENDING.value},
            )

        for plot in crud.plot.get_multi(session)[1]:
            crud.plot.update(
                session,
                db_obj=plot,
                obj_in={"status": schemas.PlotStatus.PENDING.value},
            )

        for plotting_queue in crud.plot_queue.get_multi(session)[1]:
            if plotting_queue.status not in [
                schemas.PlotQueueStatus.PAUSED.value,
                schemas.PlotQueueStatus.FAILED.value,
            ]:
                # logger.warning(
                #     f"[{plotting_queue.server.hostname}] restarting queue {plotting_queue.id}"
                # )
                # task = tasks.plot_queue_task.apply_async(
                #     (plotting_queue.id,), eta=datetime.now() + timedelta(seconds=10)
                # )
                crud.plot_queue.update(
                    session,
                    db_obj=plotting_queue,
                    obj_in={"status": schemas.PlotQueueStatus.PENDING.value},
                )
    finally:
        session.close()