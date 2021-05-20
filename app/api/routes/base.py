from typing import Any
from uuid import UUID, uuid4
import celery

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import auth
from app.core import tasks
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter


class BaseCBV:
    db: Session = Depends(deps.get_db)


class BaseAuthCBV(BaseCBV):
    # user: models.User = Depends(deps.get_current_user)
    ...
