from app.models.user import User
from datetime import timedelta
from typing import Any, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils import auth

router = APIRouter()


@router.post(
    "/access-token/",
    response_model=schemas.Token,
    responses={
        400: {"model": schemas.Error, "description": "Authentication error"},
        403: {"model": schemas.Error, "description": "Forbidden"},
    },
)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    **username** in form data is either an email or nickname.
    """

    user = crud.user.authenticate(
        db, login=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_REFRESH_EXPIRE_MINUTES
    )
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.put(
    "/access-token/",
    response_model=schemas.Token,
    responses={
        404: {"model": schemas.Error, "description": "Not found"},
    },
)
def refresh_token(
    user: models.User = Depends(deps.get_current_user_raw),
) -> Any:
    """
    Get a new access token.
    """

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_REFRESH_EXPIRE_MINUTES
    )
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


# @router.post(
#     "/password-recovery/{user_login}/",
#     response_model=schemas.Msg,
#     responses={
#         404: {"model": schemas.Error, "description": "Not found"},
#         403: {"model": schemas.Error, "description": "Forbidden"},
#     },
# )
# def recover_password(
#     user_login: schemas.UserLogin,
#     db: Session = Depends(deps.get_db),
#     i18n: str = Query(settings.EMAIL_DEFAULT_LANGUAGE),
# ) -> Any:
#     """
#     Password recovery from email, nickname or user ID.
#     """

#     user = crud.user.get_by_login(db, login=user_login)

#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="The user with this username does not exist in the system.",
#         )

#     if not user.verified:
#         raise HTTPException(403, detail="The user has not verified an email")

#     if settings.EMAILS_ENABLED:
#         password_reset_token = auth.generate_password_reset_token(
#             email=EmailStr(user.email)
#         )
#         email.send_reset_password_email.delay(
#             i18n=i18n,
#             email_to=user.email,
#             nickname=user.nickname,
#             token=password_reset_token,
#         )
#     return {"msg": "Password recovery email sent"}


# @router.post(
#     "/reset-password/",
#     response_model=schemas.Msg,
#     responses={
#         400: {"model": schemas.Error, "description": "Invalid token"},
#         404: {"model": schemas.Error, "description": "Not found"},
#         403: {"model": schemas.Error, "description": "Forbidden"},
#     },
# )
# def reset_password(
#     token: str = Body(...),
#     new_password: str = Body(...),
#     db: Session = Depends(deps.get_db),
# ) -> Any:
#     """
#     Reset password using password recovery token
#     from POST /login/password-recovery/{user_login}/
#     """
#     email = auth.verify_email_token(token)
#     if not email:
#         raise HTTPException(status_code=400, detail="Invalid token")

#     user = crud.user.get_by_email(db, email=email)

#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="The user with this username does not exist in the system.",
#         )

#     if not user.verified:
#         raise HTTPException(403, detail="The user has not verified an email")

#     crud.user.update(db, db_obj=user, obj_in={"password": new_password})

#     return {"msg": "Password updated successfully"}