from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Artifact
from app.schemas.artifact import ArtifactCreate


def create_artifact(db: Session, payload: ArtifactCreate) -> Artifact:
    artifact = Artifact(
        job_id=payload.job_id,
        image_set_id=payload.image_set_id,
        source_image_id=payload.source_image_id,
        artifact_type=payload.artifact_type,
        storage_key=payload.storage_key,
        mime_type=payload.mime_type,
        width=payload.width,
        height=payload.height,
        file_size=payload.file_size,
        metadata_json=payload.metadata,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def list_job_artifacts(db: Session, job_id: str) -> list[Artifact]:
    statement = select(Artifact).where(Artifact.job_id == job_id).order_by(Artifact.created_at)
    return list(db.scalars(statement))

