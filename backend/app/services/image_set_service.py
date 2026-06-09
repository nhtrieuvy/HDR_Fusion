from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ImageSet, SourceImage
from app.schemas.image_set import ImageSetCreate
from app.schemas.source_image import SourceImageCreate


def create_image_set(db: Session, payload: ImageSetCreate) -> ImageSet:
    image_set = ImageSet(project_id=payload.project_id, name=payload.name, capture_group=payload.capture_group)
    db.add(image_set)
    db.commit()
    db.refresh(image_set)
    return image_set


def get_image_set(db: Session, image_set_id: str) -> ImageSet | None:
    return db.get(ImageSet, image_set_id)


def list_source_images(db: Session, image_set_id: str) -> list[SourceImage]:
    statement = select(SourceImage).where(SourceImage.image_set_id == image_set_id).order_by(SourceImage.created_at)
    return list(db.scalars(statement))


def register_source_image(db: Session, payload: SourceImageCreate) -> SourceImage:
    meta = payload.metadata or {}
    source = SourceImage(
        image_set_id=payload.image_set_id,
        storage_key=payload.storage_key,
        original_filename=payload.original_filename,
        mime_type=payload.mime_type,
        file_size=payload.file_size,
        raw_format=Path(payload.original_filename).suffix.lower().lstrip(".") or None,
        camera_make=meta.get("camera_make"),
        camera_model=meta.get("camera_model"),
        lens_model=meta.get("lens_model"),
        width=meta.get("width"),
        height=meta.get("height"),
        iso=meta.get("iso"),
        aperture=meta.get("aperture"),
        exposure_time=meta.get("exposure_time"),
        exposure_bias=meta.get("exposure_bias"),
        focal_length=meta.get("focal_length"),
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

