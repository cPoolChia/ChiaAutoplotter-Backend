from .server_init import server_connect_task
from .plot_queue import plot_queue_task
from .plot_scan import scan_plots_task

from app.celery import celery as celery_app


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, server_connect_task.s())
    sender.add_periodic_task(120.0, plot_queue_task.s())
    sender.add_periodic_task(60.0, scan_plots_task.s())
