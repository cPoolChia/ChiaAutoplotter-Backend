"""
This module contains tests for 
DELETE /server/{server_id}/

- Test normal
- Test directories linked
- Test no auth
"""
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
    response = client.delete(f"/server/{server.id}/", headers=user.auth_header)
    assert response.status_code == 200, response.content
    assert crud.server.get(db, id=server.id) is None


def test_directories_linked(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=TEST_SERVER_CREATE)
    directory = crud.directory.create(
        db,
        obj_in=schemas.DirectoryCreateExtended(
            location="/root/plotting", server_id=server.id
        ),
    )
    response = client.delete(f"/server/{server.id}/", headers=user.auth_header)
    assert response.status_code == 403, response.content
    assert crud.server.get(db, id=server.id) is not None


def test_no_auth(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=TEST_SERVER_CREATE)
    response = client.delete(f"/server/{server.id}/")
    assert response.status_code == 401, response.content
    assert crud.server.get(db, id=server.id) is not None