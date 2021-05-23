from __future__ import annotations

import time
from typing import Any, Iterator, Optional, Union
from uuid import UUID
from pydantic import EmailStr

import pytest
import os
from fastapi.encoders import jsonable_encoder
from app import app as fast_api
from app import db as db_module, schemas, models, crud
from app.api.deps import get_db
from app.core.config import settings
from app.utils import auth, repeats
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
@repeats(60)
def db() -> Session:
    schema_name = f"test_{round(time.time()*100000)}_{os.getpid()}"
    engine = create_engine(settings.SQLALCHEMY_DATABASE.replace("/main", ""))

    with engine.connect() as connection:
        connection.execute(f"CREATE DATABASE IF NOT EXISTS {schema_name}")

    engine = create_engine(settings.SQLALCHEMY_DATABASE.replace("main", schema_name))
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    db_module.init_db(session)
    return session


class ExtendedTestClient(TestClient):
    def request(self, *args, json: Any = None, **kwargs) -> requests.Response:  # type: ignore
        if json is not None:
            return super().request(*args, **kwargs, json=jsonable_encoder(json))
        return super().request(*args, **kwargs, json=json)


@pytest.fixture()
def client(db: Session) -> TestClient:
    def override_get_db() -> Iterator[Session]:
        try:
            yield db
        finally:
            db.close()

    fast_api.dependency_overrides[get_db] = override_get_db
    return ExtendedTestClient(fast_api)


class BaseUser:
    def __init__(self, client: TestClient, login: str, password: str) -> None:
        self._client = client
        self.login = login
        self.password = password


class User(BaseUser):
    def __init__(self, client: TestClient, login: str, password: str) -> None:
        super().__init__(client, login, password)

        data = schemas.UserReturn(
            **self._client.get("/user/", headers=self.auth_header).json()
        )
        self.id = data.id

    def __eq__(self, other: Union[User, Any]) -> bool:
        if not isinstance(other, User):
            return super().__eq__(other)

        return self.id == other.id

    @property
    def token(self) -> str:
        token_request = self._client.post(
            "/login/access-token/",
            data={"username": self.login, "password": self.password},
        )
        assert token_request.status_code == 200, token_request.content
        data = schemas.Token(**token_request.json())
        return data.access_token

    @property
    def auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


@pytest.fixture
def user(client: TestClient) -> User:
    return User(client, login=settings.ADMIN_NAME, password=settings.ADMIN_PASSWORD)