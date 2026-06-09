from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="raw_hdr.run_qc")
def run_qc(job_id: str):
    return {"job_id": job_id, "status": "qc_is_executed_inside_full_pipeline"}

