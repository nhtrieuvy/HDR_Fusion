from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.versions import PIPELINE_NAME, PIPELINE_VERSION
from app.db.models import Job, JobStep
from app.schemas.job import JobCreate


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_job(db: Session, payload: JobCreate, config_snapshot: dict[str, Any]) -> Job:
    params = dict(payload.params or {})
    if payload.mode:
        params.setdefault("mode", payload.mode)
    job = Job(
        image_set_id=payload.image_set_id,
        status="queued",
        progress=0.0,
        pipeline_name=payload.pipeline_name or PIPELINE_NAME,
        pipeline_version=PIPELINE_VERSION,
        preset_name=payload.preset_name,
        preset_version=str(config_snapshot.get("version", "1.0.0")),
        params=params,
        config_snapshot=config_snapshot,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Job | None:
    return db.get(Job, job_id)


def list_jobs(db: Session, limit: int = 100) -> list[Job]:
    statement = select(Job).order_by(Job.created_at.desc()).limit(limit)
    return list(db.scalars(statement))


def list_job_steps(db: Session, job_id: str) -> list[JobStep]:
    statement = select(JobStep).where(JobStep.job_id == job_id).order_by(JobStep.started_at)
    return list(db.scalars(statement))


def mark_job_running(db: Session, job: Job) -> Job:
    job.status = "running"
    job.progress = max(job.progress, 5.0)
    job.started_at = job.started_at or utcnow()
    job.error_message = None
    db.commit()
    db.refresh(job)
    return job


def update_job_progress(db: Session, job: Job, progress: float) -> Job:
    job.progress = max(job.progress, progress)
    db.commit()
    db.refresh(job)
    return job


def mark_job_completed(db: Session, job: Job, output_artifact_id: str | None, status: str = "completed") -> Job:
    job.status = status
    job.progress = 100.0
    job.output_artifact_id = output_artifact_id
    job.completed_at = utcnow()
    db.commit()
    db.refresh(job)
    return job


def mark_job_failed(db: Session, job: Job, error_message: str) -> Job:
    job.status = "failed"
    job.error_message = error_message
    job.completed_at = utcnow()
    db.commit()
    db.refresh(job)
    return job


def reset_job_for_retry(db: Session, job: Job, preset_name: str | None = None) -> Job:
    job.status = "queued"
    job.progress = 0.0
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    if preset_name:
        job.preset_name = preset_name
    db.commit()
    db.refresh(job)
    return job


def start_step(db: Session, job_id: str, step_name: str, progress: float) -> JobStep:
    step = JobStep(job_id=job_id, step_name=step_name, status="running", progress=progress, started_at=utcnow())
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def complete_step(
    db: Session,
    step: JobStep,
    metrics: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    artifacts: dict[str, Any] | None = None,
) -> JobStep:
    step.status = "completed"
    step.metrics = metrics or {}
    step.warnings = warnings or []
    step.artifacts = artifacts or {}
    step.completed_at = utcnow()
    db.commit()
    db.refresh(step)
    return step


def fail_step(db: Session, step: JobStep, error_message: str, metrics: dict[str, Any] | None = None) -> JobStep:
    step.status = "failed"
    step.error_message = error_message
    step.metrics = metrics or {}
    step.completed_at = utcnow()
    db.commit()
    db.refresh(step)
    return step
