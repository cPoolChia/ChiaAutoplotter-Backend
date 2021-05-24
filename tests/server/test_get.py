"""
This module contains tests for 
GET /server/

- Test empty
- Test few
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


def test_empty(db: Session, client: TestClient, user: User) -> None:
    server_num, _ = crud.server.get_multi(db)
    assert server_num == 0

    response = client.get("/server/", headers=user.auth_header)
    assert response.status_code == 200, response.content

    table = schemas.Table[schemas.ServerReturn](**response.json())
    assert table.amount == 0
    assert table.items == []


def test_few(db: Session, client: TestClient, user: User) -> None:
    id_order: list[uuid.UUID] = []
    for i, server_create in enumerate(create_test_server_schema(j) for j in range(10)):
        last_created_server = crud.server.create(db, obj_in=server_create)
        id_order.append(last_created_server.id)
        response = client.get("/server/", headers=user.auth_header)
        assert response.status_code == 200, response.content

        table = schemas.Table[schemas.ServerReturn](**response.json())
        assert table.amount == i + 1
        amount, servers = crud.server.get_multi(db)
        assert amount == i + 1
        for order_id, server_obj, server_return in zip(id_order, servers, table.items):
            assert server_return == schemas.ServerReturn.from_orm(server_obj)
            assert server_obj.id == server_return.id == order_id


def test_no_auth(db: Session, client: TestClient, user: User) -> None:
    response = client.get("/server/")
    assert response.status_code == 401, response.content