import os

from celery import Celery

from app.config.config import settings

redis_url = settings.CELERY_BROKER_URL or settings.REDIS_URI
backend = settings.CELERY_RESULT_BACKEND or redis_url

celery_app = Celery(
    "offshore_worker",
    broker=redis_url,
    backend=backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)
