from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "hdr_fusion",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks.raw_hdr_tasks", "app.workers.tasks.qc_tasks", "app.workers.tasks.export_tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=settings.broker_connection_retry_on_startup,
    task_always_eager=settings.celery_task_always_eager,
)

