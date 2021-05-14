from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.base_class import Base
from app.utils.repeater import repeats
from fastapi.logger import logger
from app import schemas
from app.core.config import settings


@repeats(amount=3, delay=20, message="Could not init database", logger=logger)
def init_db(db: Session) -> None:
    from app import crud

    try:
        Base.metadata.create_all(bind=db.bind)
        if crud.user.get_by_nickname(db, nickname=settings.ADMIN_NAME) is None:
            logger.info(
                "Creating new admin user, "
                f"as no existing with {settings.ADMIN_NAME} was found"
            )
            crud.user.create(
                db,
                obj_in=schemas.UserCreate(
                    nickname=settings.ADMIN_NAME,
                    password=settings.ADMIN_PASSWORD,
                ),
            )
    except SQLAlchemyError:
        db.rollback()
        raise
