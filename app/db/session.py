from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE, pool_pre_ping=True)
DatabaseSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)