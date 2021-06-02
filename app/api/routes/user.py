from typing import Any

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import auth
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from app.api.routes.base import BaseAuthCBV


router = InferringRouter()


@cbv(router)
class UserCBV(BaseAuthCBV):
    @router.get("/")
    def get_user_data(
        self,
        user: models.User = Depends(deps.get_current_user),
    ) -> schemas.UserReturn:
        """ Get your user data. """

        return schemas.UserReturn.from_orm(user)

    @router.put("/")
    def update_user_data(
        self,
        user: models.User = Depends(deps.get_current_user),
        data: schemas.UserUpdate = Depends(),
    ) -> schemas.UserReturn:
        user = crud.user.update(self.db, db_obj=user, obj_in=data)
        return schemas.UserReturn.from_orm(user)