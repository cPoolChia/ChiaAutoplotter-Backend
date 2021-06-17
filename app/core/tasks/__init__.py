from .server_ping import server_ping_task
from .plot_queue import plot_queue_task

from app.celery import celery as celery_app


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(30.0, server_ping_task.s())
    sender.add_periodic_task(30.0, plot_queue_task.s())
