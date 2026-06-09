from __future__ import annotations

from app.db.session import SessionLocal
from app.pipelines.raw_hdr_fusion.pipeline import RawHDRFusionPipeline
from app.workers.celery_app import celery_app


@celery_app.task(name="raw_hdr.run_input_audit")
def run_input_audit(job_id: str):
    with SessionLocal() as db:
        return RawHDRFusionPipeline(db).run_input_audit(job_id)


@celery_app.task(name="raw_hdr.run_raw_hdr_fusion")
def run_raw_hdr_fusion(job_id: str):
    with SessionLocal() as db:
        return RawHDRFusionPipeline(db).run_raw_hdr_fusion(job_id)


@celery_app.task(name="raw_hdr.run_full_pipeline")
def run_full_pipeline(job_id: str):
    with SessionLocal() as db:
        return RawHDRFusionPipeline(db).run(job_id)

