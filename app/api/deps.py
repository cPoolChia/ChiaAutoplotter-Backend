from app.db.base_class import Base
from typing import Callable, Iterator, Optional, Union, cast, Type, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app import crud, models, schemas
from app.core import security
from app.core.celery_listener import CeleryEventsListener
from app.core.config import settings
from app.db.session import DatabaseSession
from app.celery import celery as celery_app

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"/login/access-token")


def get_events_listener() -> CeleryEventsListener:
    celery_events_listener = CeleryEventsListener(celery_app)
    celery_events_listener.start_threaded()
    return celery_events_listener


def get_db() -> Iterator[Session]:
    db = DatabaseSession()
    try:
        yield db
    finally:
        db.close()


def get_token_data(token: str = Depends(reusable_oauth2)) -> schemas.AuthTokenPayload:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.AuthTokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        ) from error
    return token_data


def get_current_user_raw(
    db: Session = Depends(get_db),
    token_data: schemas.AuthTokenPayload = Depends(get_token_data),
) -> models.User:
    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_user(
    token_data: schemas.AuthTokenPayload = Depends(get_token_data),
    user: models.User = Depends(get_current_user_raw),
) -> models.User:
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_REFRESH_EXPIRE_MINUTES
    )
    token_login_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_login_expires_date = (
        token_data.exp - access_token_expires + token_login_expires
    )
    if datetime.now(token_login_expires_date.tzinfo) > token_login_expires_date:
        raise HTTPException(403, detail="Login time for token has been expired")
    return user


def get_filtration_data(_T: Optional[Type[Base]] = None) -> Callable:
    def dependancy(
        *,
        limit: int = 100,
        offset: int = 0,
        sort: Optional[str] = None,
        request: Request,
    ) -> schemas.FilterData[_T]:
        res = schemas.FilterData(
            table=_T,
            limit=limit,
            offset=offset,
            sort=sort,  # type: ignore
            data=dict(request.query_params.items()),
        )
        return res

    return dependancy


def get_server_by_id(server_id: UUID, db: Session = Depends(get_db)) -> models.Server:
    server = crud.server.get(db, server_id)
    if server is None:
        raise HTTPException(404, "Server with such id is not found")
    return server


def get_plot_queue_by_id(
    plot_queue_id: UUID, db: Session = Depends(get_db)
) -> models.Server:
    plot_queue = crud.plot_queue.get(db, plot_queue_id)
    if plot_queue is None:
        raise HTTPException(404, "Plot queue with such id is not found")
    return plot_queue