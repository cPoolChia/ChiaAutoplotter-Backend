from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.db.session import DatabaseSession
from app.db import init_db
from app.core.config import settings
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

if not settings.SKIP_DB_INIT:
    init_db(DatabaseSession())
else:
    logger.info("Skipped database init (settings.SKIP_DB_INIT == True)")