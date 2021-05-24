"""
This module contains tests for 
POST /server/

- Test normal
- Test same name
- Test same hostname
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
    servers_count_start, _ = crud.server.get_multi(db)
    response = client.post(
        "/server/", json=TEST_SERVER_CREATE, headers=user.auth_header
    )
    assert response.status_code == 201, response.content
    response_data = schemas.ServerReturn(**response.json())
    assert schemas.ServerCreate(**response_data.dict()) == TEST_SERVER_CREATE
    server = crud.server.get(db, id=response_data.id)
    assert server is not None
    assert response_data.status == schemas.ServerStatus.PENDING
    servers_count_end, _ = crud.server.get_multi(db)
    assert servers_count_start + 1 == servers_count_end


def test_name_collision(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=TEST_SERVER_CREATE)
    servers_count_start, _ = crud.server.get_multi(db)
    server_different_host = schemas.ServerCreate(
        **(TEST_SERVER_CREATE.dict() | dict(hostname="192.168.1.1"))
    )
    response = client.post(
        "/server/", json=server_different_host, headers=user.auth_header
    )
    assert response.status_code == 403
    servers_count_end, _ = crud.server.get_multi(db)
    assert servers_count_start == servers_count_end


def test_hostname_collision(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=TEST_SERVER_CREATE)
    servers_count_start, _ = crud.server.get_multi(db)
    server_different_host = schemas.ServerCreate(
        **(TEST_SERVER_CREATE.dict() | dict(name="Other test server"))
    )
    response = client.post(
        "/server/", json=server_different_host, headers=user.auth_header
    )
    assert response.status_code == 403
    servers_count_end, _ = crud.server.get_multi(db)
    assert servers_count_start == servers_count_end


def test_no_auth(db: Session, client: TestClient, user: User) -> None:
    servers_count_start, _ = crud.server.get_multi(db)
    response = client.post("/server/", json=TEST_SERVER_CREATE)
    assert response.status_code == 401, response.content
    servers_count_end, _ = crud.server.get_multi(db)
    assert servers_count_start == servers_count_end