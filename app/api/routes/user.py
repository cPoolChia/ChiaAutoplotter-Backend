from typing import Any

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import auth
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/",
    response_model=schemas.UserReturn,
    responses={403: {"model": schemas.Error, "description": "Forbidden"}},
)
def get_user_data(
    user: models.User = Depends(deps.get_current_user),
) -> Any:
    """ Get your user data. """

    return user.__dict__