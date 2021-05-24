"""
This module contains tests for 
PUT /server/{server_id}/

- Test normal
- Test already connected
- Test invalid id
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


def test_normal(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=TEST_SERVER_CREATE)
    server_update = schemas.ServerUpdate(hostname="192.168.228.123")
    response = client.put(
        f"/server/{server.id}/", json=server_update, headers=user.auth_header
    )
    assert response.status_code == 200, response.content

    server = crud.server.get(db, id=server.id)
    response_result = schemas.ServerReturn(**response.json())
    assert response_result == schemas.ServerReturn.from_orm(server)
    assert response_result.hostname == server_update.hostname


def test_already_connected(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=TEST_SERVER_CREATE)
    server = crud.server.update(
        db, db_obj=server, obj_in={"status": schemas.ServerStatus.CONNECTED.value}
    )
    server_update = schemas.ServerUpdate(hostname="192.168.228.123")
    response = client.put(
        f"/server/{server.id}/", json=server_update, headers=user.auth_header
    )
    assert response.status_code == 403, response.content
    assert schemas.ServerReturn.from_orm(
        crud.server.get(db, id=server.id)
    ) == schemas.ServerReturn.from_orm(server)
    assert server.hostname == TEST_SERVER_CREATE.hostname


def test_invalid_id(db: Session, client: TestClient, user: User) -> None:
    server_update = schemas.ServerUpdate(hostname="192.168.228.123")
    response = client.put(
        f"/server/{uuid.uuid4()}/", json=server_update, headers=user.auth_header
    )
    assert response.status_code == 404, response.content


def test_no_auth(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=TEST_SERVER_CREATE)
    server_update = schemas.ServerUpdate(hostname="192.168.228.123")
    response = client.put(f"/server/{server.id}/", json=server_update)
    assert response.status_code == 401, response.content
    assert schemas.ServerReturn.from_orm(
        crud.server.get(db, id=server.id)
    ) == schemas.ServerReturn.from_orm(server)
    assert server.hostname == TEST_SERVER_CREATE.hostname