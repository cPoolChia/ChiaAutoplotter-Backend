"""
This module contains tests for 
POST /server/{server_id}/directory/

- Test normal
- Test invalid server id
- Test existing
- Test no auth
"""

from pydantic.schema import schema
from tests import Session, TestClient, User
from app import crud, schemas, models
import uuid


def create_test_server_schema(number: int) -> schemas.ServerCreate:
    return schemas.ServerCreate(
        name=f"Test server {number}",
        hostname=f"127.0.0.{number}",
        username="root",
        password="12345",
        pool_key="0x0",
        farmer_key="0x0",
    )


def test_normal(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=create_test_server_schema(1))
    create_schema = schemas.DirectoryCreate(location=f"/root/plotting/")
    response = client.post(
        f"/server/{server.id}/directory/",
        headers=user.auth_header,
        json=create_schema,
    )
    assert response.status_code == 201, response.content
    response_data = schemas.DirectoryReturn(**response.json())
    assert response_data.location == create_schema.location
    assert response_data.status == schemas.DirectoryStatus.PENDING
    assert response_data.server_id == server.id


def test_invalid_server_id(db: Session, client: TestClient, user: User) -> None:
    response = client.post(
        f"/server/{uuid.uuid4()}/directory/",
        headers=user.auth_header,
        json=schemas.DirectoryCreate(location=f"/root/plotting/"),
    )
    assert response.status_code == 404, response.content


def test_existing(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=create_test_server_schema(1))
    create_schema = schemas.DirectoryCreate(location=f"/root/plotting/")
    response = client.post(
        f"/server/{server.id}/directory/",
        headers=user.auth_header,
        json=create_schema,
    )
    assert response.status_code == 201, response.content
    response = client.post(
        f"/server/{server.id}/directory/",
        headers=user.auth_header,
        json=create_schema,
    )
    assert response.status_code == 403, response.content


def test_no_auth(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=create_test_server_schema(1))
    create_schema = schemas.DirectoryCreate(location=f"/root/plotting/")
    response = client.post(f"/server/{server.id}/directory/", json=create_schema)
    assert response.status_code == 401, response.content