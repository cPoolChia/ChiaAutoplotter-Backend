from app.core.console.log_collector import ConsoleLogCollector
from app.schemas.directory import DirectoryReturn
from typing import Any, Callable, Optional, cast


import pathlib
import celery
import requests
import time
import uuid
from app import schemas, crud
from app.celery import celery as celery_app
from sqlalchemy.orm import Session
from app.db.session import DatabaseSession, session_manager


@celery_app.task(bind=True)
def server_ping_task(
    self: celery.Task,
    *,
    session_factory: Callable[[], Session] = DatabaseSession,
) -> Any:
    with session_manager(session_factory) as db:
        server_ids = [server.id for server in crud.server.get_multi(db)[1]]
    log_collector = ConsoleLogCollector()

    for server_id in server_ids:
        with session_manager(session_factory) as db:
            server = crud.server.get(db, id=server_id)
            if server is None:
                raise RuntimeError(
                    f"Can not find a server data with id {server_id} in a database"
                )

            server_data = schemas.ServerReturn.from_orm(server)

            _, directory_objects = crud.directory.get_multi_by_server(db, server=server)
            directories: dict[str, uuid.UUID] = {
                schemas.DirectoryReturn.from_orm(directory).location: directory.id
                for directory in directory_objects
            }

            host = server_data.hostname.split(":")[0]
            worker_password = server.worker_password
            worker_port = server.worker_port
            uri = f"http://{host}:{worker_port}"

        # Connect to server and get a token
        try:
            log_collector.update_log(
                stdout=f"\nPOST {uri}/login/access-token/\n".encode("utf8")
            )
            login_responce = requests.post(
                f"{uri}/login/access-token/",
                data={"username": "admin", "password": worker_password},
            )
        except requests.exceptions.ConnectionError:
            log_collector.update_log(
                stdout=f"\n Can not connect to {uri} \n".encode("utf8")
            )
            with session_manager(session_factory) as db:
                server = crud.server.get(db, id=server_id)
                if server is None:
                    raise RuntimeError(f"Server with id {server_id} has gone away")
                server = crud.server.update(
                    db, db_obj=server, obj_in={"status": "failed"}
                )
            continue
        else:
            log_collector.update_log(stdout=login_responce.content)
            if not login_responce.ok:
                register_request = requests.post(
                    f"{uri}/user/",
                    json={"nickname": "admin", "password": worker_password},
                )
                log_collector.update_log(
                    stdout=f"\nPOST {register_request.url}\n".encode("utf8")
                )
                log_collector.update_log(stdout=register_request.content)
                if not register_request.ok:
                    with session_manager(session_factory) as db:
                        server = crud.server.get(db, id=server_id)
                        if server is None:
                            raise RuntimeError(
                                f"Server with id {server_id} has gone away"
                            )
                        server = crud.server.update(
                            db, db_obj=server, obj_in={"status": "failed"}
                        )
                    continue
                login_responce = requests.post(
                    f"{uri}/login/access-token/",
                    data={"username": "admin", "password": worker_password},
                )
                if not login_responce.ok:
                    raise RuntimeError(
                        "Unexpected register: "
                        "registration was successful, "
                        "but login is impossible"
                    )
            with session_manager(session_factory) as db:
                server = crud.server.get(db, id=server_id)
                if server is None:
                    raise RuntimeError(f"Server with id {server_id} has gone away")
                server = crud.server.update(
                    db, db_obj=server, obj_in={"status": "connected"}
                )

        token_data = schemas.Token(**login_responce.json())
        auth_headers = {"Authorization": f"Bearer {token_data.access_token}"}

        # Try too load metadata
        metadata_responce = requests.get(f"{uri}/metadata/", headers=auth_headers)
        log_collector.update_log(
            stdout=f"\nGET {metadata_responce.url}\n".encode("utf8")
        )
        log_collector.update_log(stdout=metadata_responce.content)

        with session_manager(session_factory) as db:
            server = crud.server.get(db, id=server_id)
            if server is None:
                raise RuntimeError(f"Server with id {server_id} has gone away")

            if metadata_responce.status_code == 404:
                server = crud.server.update(
                    db, db_obj=server, obj_in={"worker_version": "< 0.1.0"}
                )
            elif metadata_responce.status_code == 200:
                server = crud.server.update(
                    db,
                    db_obj=server,
                    obj_in={"worker_version": metadata_responce.json()["version"]},
                )
            else:
                server = crud.server.update(
                    db, db_obj=server, obj_in={"worker_version": "undefined"}
                )

        directories_request = requests.post(
            f"{uri}/directories/", json={"directories": list(directories.values())}
        )

        if not directories_request.ok:
            server = crud.server.get(db, id=server_id)
            if server is None:
                raise RuntimeError(f"Server with id {server_id} has gone away")
            server = crud.server.update(
                db,
                db_obj=server,
                obj_in={"worker_version": f"{server.worker_version} (unsupported)"},
            )

        dir_data: dict[pathlib.Path, Optional[schemas.DirInfo]] = {
            pathlib.Path(path): res and schemas.DirInfo(**res)
            for path, res in directories_request.json()
        }

        with session_manager(session_factory) as db:
            for loc, data in dir_data.items():
                directory = crud.directory.get(db, id=directories[loc.name])
                if directory is None:
                    continue

                if data is None:
                    directory = crud.directory.update(
                        db, db_obj=directory, obj_in={"status": "failed"}
                    )
                    continue

                directory = crud.directory.update(
                    db,
                    db_obj=directory,
                    obj_in={
                        "status": "monitoring",
                        "disk_size": data.disk_size and data.disk_size.total,
                        "disk_taken": data.disk_size and data.disk_size.used,
                    },
                )

                for plot in data.plots:
                    plot_obj = crud.plot.get_by_name(db, name=plot.name)
                    if plot_obj is None:
                        crud.plot.create(
                            db,
                            obj_in=schemas.PlotCreate(
                                name=plot.name,
                                created_queue_id=plot.queue,
                                located_directory_id=directory.id,
                                status=schemas.PlotStatus.PLOTTING
                                if plot.plotting
                                else schemas.PlotStatus.PLOTTED,
                            ),
                        )
                    else:
                        plot_obj = crud.plot.update(
                            db,
                            db_obj=plot_obj,
                            obj_in={
                                "located_directory_id": directory.id,
                                "status": schemas.PlotStatus.PLOTTED.value
                                if plot_obj.status == schemas.PlotStatus.PLOTTING.value
                                and not plot.plotting
                                else plot_obj.status,
                            },
                        )

    return {"info": "done", "console": log_collector.get()}
