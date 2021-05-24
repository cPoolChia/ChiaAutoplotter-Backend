"""
This module contains tests for 
GET /server/{server_id}/directory/

- Test empty
- Test few
- Test not added from other servers
- Test invalid server id
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


def create_directory_schema(number: int, server_id: uuid.UUID) -> schemas.ServerCreate:
    return schemas.DirectoryCreateExtended(
        location=f"/root/plotting/{number}/", server_id=server_id
    )


def test_empty(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=create_test_server_schema(1))
    dir_num, _ = crud.directory.get_multi(db)
    assert dir_num == 0

    response = client.get(f"/server/{server.id}/directory/", headers=user.auth_header)
    assert response.status_code == 200, response.content

    table = schemas.Table[schemas.DirectoryReturn](**response.json())
    assert table.amount == 0
    assert table.items == []


def test_invalid_server_id(db: Session, client: TestClient, user: User) -> None:
    response = client.get(
        f"/server/{uuid.uuid4()}/directory/", headers=user.auth_header
    )
    assert response.status_code == 404, response.content


def test_few(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=create_test_server_schema(1))
    id_order: list[uuid.UUID] = []
    for i, dir_create in enumerate(
        create_directory_schema(j, server.id) for j in range(10)
    ):
        last_created_directory = crud.directory.create(db, obj_in=dir_create)
        id_order.append(last_created_directory.id)
        response = client.get(
            f"/server/{server.id}/directory/", headers=user.auth_header
        )
        assert response.status_code == 200, response.content

        table = schemas.Table[schemas.DirectoryReturn](**response.json())
        assert table.amount == i + 1
        amount, dirs = crud.directory.get_multi_by_server(db, server=server)
        assert amount == i + 1
        for order_id, server_obj, server_return in zip(id_order, dirs, table.items):
            assert server_return == schemas.DirectoryReturn.from_orm(server_obj)
            assert server_obj.id == server_return.id == order_id


def test_no_overlaps(db: Session, client: TestClient, user: User) -> None:
    one_server = crud.server.create(db, obj_in=create_test_server_schema(1))
    other_server = crud.server.create(db, obj_in=create_test_server_schema(2))
    crud.directory.create(db, obj_in=create_directory_schema(1, one_server.id))
    response = client.get(
        f"/server/{other_server.id}/directory/", headers=user.auth_header
    )
    assert response.status_code == 200, response.content
    table = schemas.Table[schemas.DirectoryReturn](**response.json())
    assert table.amount == 0
    assert table.items == []


def test_no_auth(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=create_test_server_schema(1))
    response = client.get(f"/server/{server.id}/directory/")
    assert response.status_code == 401, response.content