from app.core.console.log_collector import ConsoleLogCollector
from app.schemas.directory import DirectoryReturn
from typing import Any, Callable, TypedDict

import celery
import requests
import time
from uuid import UUID
from app import schemas, crud
from app.core import console
from app.api import deps
from app.celery import celery as celery_app
from sqlalchemy.orm import Session
from app.db.session import DatabaseSession, session_manager


@celery_app.task(bind=True)
def server_connect_task(
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

            directory_objects = crud.directory.get_multi_by_server(db, server=server)[1]
            directories = [
                schemas.DirectoryReturn.from_orm(directory)
                for directory in directory_objects
            ]

        def on_failed() -> None:
            with session_manager(session_factory) as db:
                server = crud.server.get(db, id=server_id)
                if server is None:
                    return
                crud.server.update(db, db_obj=server, obj_in={"status": "failed"})
                for directory in directories:
                    directory_obj = crud.directory.get(db, id=directory.id)
                    if directory_obj is None:
                        continue
                    crud.directory.update(
                        db, db_obj=directory_obj, obj_in={"status": "failed"}
                    )

        connection = console.ConnectionManager(
            server_data, self, on_failed=on_failed, log_collector=log_collector
        )

        if not connection.available():
            continue

        with connection:
            with session_manager(session_factory) as db:
                server = crud.server.get(db, id=server_id)
                if server is None:
                    raise RuntimeError(f"Server with id {server_id} has gone away")
                server = crud.server.update(
                    db, db_obj=server, obj_in={"status": "connected"}
                )

            # root_folders = connection.command.ls(dirname="/root")
            # if "chia-blockchain" not in root_folders:
            #     connection.command.chia.install()

            # if "ChiaAutoplotter-Worker" not in root_folders:
            #     connection.command.worker()

            host = server_data.hostname.split(":")[0]
            worker_password = server.worker_password
            worker_port = server.worker_port

            login_responce = requests.post(
                f"http://{host}:{worker_port}/login/access-token/",
                data={"username": "admin", "password": worker_password},
            )
            log_collector.update_log(
                stdout=f"\nPOST {login_responce.url}\n".encode("utf8")
            )
            log_collector.update_log(stdout=login_responce.content)

            metadata_responce = requests.get(
                f"http://{host}:{worker_port}/metadata/",
                data={"username": "admin", "password": worker_password},
            )
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

            if not login_responce.ok:
                uri = f"http://{host}:{worker_port}/user/"
                register_request = requests.post(
                    f"http://{host}:{worker_port}/user/",
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

            for directory in directories:
                try:
                    filenames = connection.command.ls(dirname=directory.location)
                except NotADirectoryError:
                    with session_manager(session_factory) as db:
                        directory_obj = crud.directory.get(db, id=directory.id)
                        if directory_obj is not None:
                            directory_obj = crud.directory.update(
                                db, db_obj=directory_obj, obj_in={"status": "failed"}
                            )
                else:
                    df = connection.command.df(dirname=directory.location)
                    with session_manager(session_factory) as db:
                        directory_obj = crud.directory.get(db, id=directory.id)
                        directory_obj = crud.directory.update(
                            db, db_obj=directory_obj, obj_in={"status": "monitoring"}
                        )
                        standalone_plots = {
                            filename
                            for filename in filenames
                            if filename.endswith(".plot")
                        }
                        for plot_name in standalone_plots:
                            plot = crud.plot.get_by_name(db, name=plot_name)
                            if plot is None:
                                crud.plot.create(
                                    db,
                                    obj_in=schemas.PlotCreate(
                                        name=plot_name,
                                        created_queue_id=None,
                                        located_directory_id=directory.id,
                                        status=schemas.PlotStatus.PLOTTED,
                                    ),
                                )
                        total_used = sum(line["used"] for line in df)
                        total_size = sum(line["total"] for line in df)
                        directory_obj = crud.directory.update(
                            db,
                            db_obj=directory_obj,
                            obj_in={
                                "disk_size": total_size,
                                "disk_taken": total_used,
                            },
                        )

    return {"info": "done", "console": log_collector.get()}
