"""
This module contains tests for 
GET /server/{server_id}/

- Test existing
- Test not existing
- Test no auth
"""

from pydantic.schema import schema
from tests import Session, TestClient, User
from app import crud, schemas, models
import uuid

TEST_SERVER_CREATE = schemas.ServerCreate(
    name="Test server",
    hostname="127.0.0.1",
    username="root",
    password="12345",
    pool_key="0x0",
    farmer_key="0x0",
)


def test_existing(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=TEST_SERVER_CREATE)
    response = client.get(f"/server/{server.id}/", headers=user.auth_header)
    assert response.status_code == 200, response.content
    response_data = schemas.ServerReturn(**response.json())
    assert TEST_SERVER_CREATE == schemas.ServerCreate(**response_data.dict())
    assert response_data.id == server.id
    assert response_data.status == schemas.ServerStatus.PENDING


def test_not_existing(db: Session, client: TestClient, user: User) -> None:
    server_id = uuid.uuid4()
    response = client.get(f"/server/{server_id}/", headers=user.auth_header)
    assert response.status_code == 404, response.content


def test_no_auth(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=TEST_SERVER_CREATE)
    response = client.get(f"/server/{server.id}/")
    assert response.status_code == 401, response.content