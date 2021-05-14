from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.db.session import DatabaseSession
from app.db import init_db
from app.core.config import settings
from fastapi.logger import logger

app = FastAPI(
    title="efullmakt.io Rest API",
    description="An API for efullmakt.io CRM system",
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