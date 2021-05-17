import os
import secrets
from typing import Optional
from pathlib import Path

from pydantic import BaseSettings, Field, BaseModel


class AppConfig(BaseModel):
    """Application configurations."""

    VAR_A: int = 33
    VAR_B: float = 22.0


class GlobalConfig(BaseSettings):
    """Global configurations."""

    # These variables will be loaded from the .env file. However, if
    # there is a shell environment variable having the same name,
    # that will take precedence.

    APP_CONFIG: AppConfig = AppConfig()

    # define global variables with the Field class
    ENV_STATE: Optional[str] = Field(None, env="ENV_STATE")

    # environment specific variables do not need the Field class
    CELERY_BACKEND: Optional[str] = None
    CELERY_BROKER: Optional[str] = None
    SQLALCHEMY_DATABASE: Optional[str] = None
    SKIP_DB_INIT: bool = False

    SECRET_KEY: str = secrets.token_urlsafe(32)

    PROJECT_NAME: str = "admin.cpool.farm"
    SERVER_HOST: str = "admin.cpool.farm"

    CHIA_FARMER_KEY: str = "877f56cd19255d76469b0ccfbf542a552f1f4580aa41b107c71b21ef4df5226f503ba95e8d75d6d47dc296ae8d2e87e3"
    CHIA_POOL_KEY: str = "a50785ca66e2b3537ed8ee478f8dbf37a45ea5d00b50ca18f113cf5edea33f5b3a64c7633bdef1930225e98f970dce3c"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    ACCESS_TOKEN_REFRESH_EXPIRE_MINUTES: int = 60 * 24 * 7

    ADMIN_NAME: str = "admin"
    ADMIN_PASSWORD: str = "qweR1tyFUn123"

    class Config:
        """Loads the dotenv file."""

        env_file: str = ".env"


class DevConfig(GlobalConfig):
    """Development configurations."""

    class Config:
        env_prefix: str = "DEV_"


class ProdConfig(GlobalConfig):
    """Production configurations."""

    class Config:
        env_prefix: str = "PROD_"


class AloneConfig(GlobalConfig):
    """Production configurations."""

    class Config:
        env_prefix: str = "ALONE_"


env_state = os.getenv("ENV_STATE")

settings: GlobalConfig

if env_state == "prod":
    settings = ProdConfig()
elif env_state == "dev":
    settings = DevConfig()
else:
    settings = AloneConfig()