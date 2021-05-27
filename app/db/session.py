from typing import Callable
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from sqlalchemy.orm.session import Session

from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE, pool_pre_ping=True)
DatabaseSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def session_manager(session_factory: Callable[[], Session] = DatabaseSession):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()