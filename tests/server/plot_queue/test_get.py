"""
This module contains tests for 
GET /server/{server_id}/queues/

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
    queue_amount, _ = crud.plot_queue.get_multi(db)
    assert queue_amount == 0

    response = client.get(f"/server/{server.id}/queues/", headers=user.auth_header)
    assert response.status_code == 200, response.content

    table = schemas.Table[schemas.PlotQueueReturn](**response.json())
    assert table.amount == 0
    assert table.items == []


def test_invalid_server_id(db: Session, client: TestClient, user: User) -> None:
    response = client.get(f"/server/{uuid.uuid4()}/queues/", headers=user.auth_header)
    assert response.status_code == 404, response.content


def test_few(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=create_test_server_schema(1))
    final_dir_id = crud.directory.create(
        db, obj_in=create_directory_schema(1, server.id)
    ).id
    temp_dir_ids = [
        crud.directory.create(db, obj_in=create_directory_schema(1 + j, server.id)).id
        for j in range(10)
    ]
    id_order: list[uuid.UUID] = []
    create_plot_queue = lambda j: schemas.PlotQueueCreate(
        server_id=server.id,
        temp_dir_id=temp_dir_ids[j],
        final_dir_id=final_dir_id,
        plots_amount=1,
    )
    for i, queue_create in enumerate(create_plot_queue(j) for j in range(10)):
        last_created_queue = crud.plot_queue.create(db, obj_in=queue_create)
        id_order.append(last_created_queue.id)
        response = client.get(f"/server/{server.id}/queues/", headers=user.auth_header)
        assert response.status_code == 200, response.content

        table = schemas.Table[schemas.PlotQueueReturn](**response.json())
        assert table.amount == i + 1
        amount, queues = crud.plot_queue.get_multi_by_server(db, server=server)
        assert amount == i + 1
        for order_id, queue_obj, queue_return in zip(id_order, queues, table.items):
            assert queue_return == schemas.PlotQueueReturn.from_orm(queue_obj)
            assert queue_obj.id == queue_return.id == order_id


def test_no_overlaps(db: Session, client: TestClient, user: User) -> None:
    one_server = crud.server.create(db, obj_in=create_test_server_schema(1))
    other_server = crud.server.create(db, obj_in=create_test_server_schema(2))
    one_temp_dir = crud.directory.create(
        db, obj_in=create_directory_schema(1, one_server.id)
    )
    one_final_dir = crud.directory.create(
        db, obj_in=create_directory_schema(2, one_server.id)
    )
    crud.plot_queue.create(
        db,
        obj_in=schemas.PlotQueueCreate(
            server_id=one_server.id,
            plots_amount=1,
            temp_dir_id=one_temp_dir.id,
            final_dir_id=one_final_dir.id,
        ),
    )
    response = client.get(
        f"/server/{other_server.id}/queues/", headers=user.auth_header
    )
    assert response.status_code == 200, response.content
    table = schemas.Table[schemas.PlotQueueReturn](**response.json())
    assert table.amount == 0
    assert table.items == []


def test_no_auth(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=create_test_server_schema(1))
    temp_dir = crud.directory.create(db, obj_in=create_directory_schema(1, server.id))
    final_dir = crud.directory.create(db, obj_in=create_directory_schema(2, server.id))
    crud.plot_queue.create(
        db,
        obj_in=schemas.PlotQueueCreate(
            server_id=server.id,
            plots_amount=1,
            temp_dir_id=temp_dir.id,
            final_dir_id=final_dir.id,
        ),
    )
    response = client.get(f"/server/{server.id}/queues/")
    assert response.status_code == 401, response.content