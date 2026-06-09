from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="raw_hdr.run_export")
def run_export(job_id: str):
    return {"job_id": job_id, "status": "export_is_executed_inside_full_pipeline"}

