from celery import Celery

from app.core.config import settings

celery = Celery(
    __name__,
    backend=settings.CELERY_BACKEND,
    broker=settings.CELERY_BROKER,
)
celery.autodiscover_tasks(["app.core.tasks"], related_name=None)