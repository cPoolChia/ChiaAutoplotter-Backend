"""
This module contains tests for 
GET /server/{server_id}/plots/created/

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
    response = client.get(
        f"/server/{server.id}/plots/created/", headers=user.auth_header
    )
    assert response.status_code == 200, response.content
    table = schemas.Table[schemas.PlotReturn](**response.json())
    assert table.amount == 0
    assert table.items == []


def test_few(db: Session, client: TestClient, user: User) -> None:
    server_id = crud.server.create(db, obj_in=create_test_server_schema(1)).id
    final_dir_id = crud.directory.create(
        db, obj_in=create_directory_schema(1, server_id)
    ).id
    temp_dir_id = crud.directory.create(
        db, obj_in=create_directory_schema(2, server_id)
    ).id
    queue_id = crud.plot_queue.create(
        db,
        obj_in=schemas.PlotQueueCreate(
            server_id=server_id,
            temp_dir_id=temp_dir_id,
            final_dir_id=final_dir_id,
            plots_amount=1,
        ),
    ).id
    id_order: list[uuid.UUID] = []
    create_plot = lambda j: schemas.PlotCreate(
        name=f"plot-{j}",
        created_queue_id=queue_id,
        located_directory_id=final_dir_id,
        status=schemas.PlotStatus.PLOTTED,
    )

    for i in range(10):
        plot = crud.plot.create(db, obj_in=create_plot(i))
        request = client.get(
            f"/server/{server_id}/plots/created/", headers=user.auth_header
        )
        assert request.status_code == 200, request.content

        table = schemas.Table[schemas.PlotReturn](**request.json())
        assert table.amount == i + 1
        for table_item, id_in_order in zip(table.items, id_order):
            assert table_item.id == id_in_order
            assert schemas.PlotReturn.from_orm(crud.plot.get(id_in_order)) == table_item


def test_not_from_other_servers(db: Session, client: TestClient, user: User) -> None:
    server_id = crud.server.create(db, obj_in=create_test_server_schema(1)).id
    other_server_id = crud.server.create(db, obj_in=create_test_server_schema(2)).id
    final_dir_id = crud.directory.create(
        db, obj_in=create_directory_schema(1, server_id)
    ).id
    temp_dir_id = crud.directory.create(
        db, obj_in=create_directory_schema(2, server_id)
    ).id
    queue_id = crud.plot_queue.create(
        db,
        obj_in=schemas.PlotQueueCreate(
            server_id=server_id,
            temp_dir_id=temp_dir_id,
            final_dir_id=final_dir_id,
            plots_amount=1,
        ),
    ).id
    crud.plot.create(
        db,
        obj_in=schemas.PlotCreate(
            name=f"plot-12",
            created_queue_id=queue_id,
            located_directory_id=final_dir_id,
            status=schemas.PlotStatus.PLOTTED,
        ),
    )
    request = client.get(
        f"/server/{other_server_id}/plots/created/", headers=user.auth_header
    )
    assert request.status_code == 200, request.content
    table = schemas.Table[schemas.PlotReturn](**request.json())
    assert table.amount == 0
    assert table.items == []


def test_invalid_id(db: Session, client: TestClient, user: User) -> None:
    response = client.get(
        f"/server/{uuid.uuid4()}/plots/created/", headers=user.auth_header
    )
    assert response.status_code == 404, response.content


def test_invalid_id(db: Session, client: TestClient, user: User) -> None:
    server = crud.server.create(db, obj_in=create_test_server_schema(1))
    response = client.get(f"/server/{server.id}/plots/created/")
    assert response.status_code == 401, response.content