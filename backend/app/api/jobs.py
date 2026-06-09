from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import http_not_found
from app.db.session import get_db
from app.schemas.artifact import ArtifactRead
from app.schemas.job import JobCreate, JobRead, JobStepRead, ReenhanceJobRequest, RetryJobRequest
from app.services.artifact_service import list_job_artifacts
from app.services.image_set_service import get_image_set
from app.services.job_service import create_job, get_job, list_job_steps, list_jobs, reset_job_for_retry
from app.services.preset_service import load_preset, merge_params
from app.workers.tasks.raw_hdr_tasks import run_full_pipeline

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead)
def post_job(payload: JobCreate, db: Session = Depends(get_db)):
    if get_image_set(db, payload.image_set_id) is None:
        raise http_not_found("Image set not found")
    preset = merge_params(load_preset(payload.preset_name), payload.params)
    job = create_job(db, payload, config_snapshot=preset)
    _enqueue(job.id)
    return job


@router.get("", response_model=list[JobRead])
def get_jobs(limit: int = 100, db: Session = Depends(get_db)):
    return list_jobs(db, limit=max(1, min(limit, 500)))


@router.get("/{job_id}", response_model=JobRead)
def get_one_job(job_id: str, db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    if job is None:
        raise http_not_found("Job not found")
    return job


@router.get("/{job_id}/steps", response_model=list[JobStepRead])
def get_steps(job_id: str, db: Session = Depends(get_db)):
    if get_job(db, job_id) is None:
        raise http_not_found("Job not found")
    return list_job_steps(db, job_id)


@router.get("/{job_id}/results", response_model=list[ArtifactRead])
def get_results(job_id: str, db: Session = Depends(get_db)):
    if get_job(db, job_id) is None:
        raise http_not_found("Job not found")
    return list_job_artifacts(db, job_id)


@router.post("/{job_id}/retry", response_model=JobRead)
def retry_job(job_id: str, payload: RetryJobRequest | None = None, db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    if job is None:
        raise http_not_found("Job not found")
    reset_job_for_retry(db, job, preset_name=(payload.preset_name if payload else None))
    _enqueue(job.id)
    return job


@router.post("/{job_id}/reenhance", response_model=JobRead)
def reenhance_job(job_id: str, payload: ReenhanceJobRequest | JobCreate | None = None, db: Session = Depends(get_db)):
    original = get_job(db, job_id)
    if original is None:
        raise http_not_found("Job not found")
    if isinstance(payload, JobCreate):
        request = payload
    else:
        request = JobCreate(
            image_set_id=original.image_set_id,
            preset_name=(payload.preset_name if payload else original.preset_name),
            mode=(payload.mode if payload else "quality"),
            params=(payload.params if payload else {}),
        )
    preset = merge_params(load_preset(request.preset_name), request.params)
    job = create_job(db, request, config_snapshot=preset)
    _enqueue(job.id)
    return job


def _enqueue(job_id: str) -> None:
    try:
        run_full_pipeline.delay(job_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to enqueue job: {exc}",
        ) from exc
