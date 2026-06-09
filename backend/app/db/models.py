from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.versions import PIPELINE_NAME, PIPELINE_VERSION
from app.db.session import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    projects: Mapped[list[Project]] = relationship(back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User | None] = relationship(back_populates="projects")
    image_sets: Mapped[list[ImageSet]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ImageSet(Base):
    __tablename__ = "image_sets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capture_group: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped[Project] = relationship(back_populates="image_sets")
    source_images: Mapped[list[SourceImage]] = relationship(back_populates="image_set", cascade="all, delete-orphan")
    jobs: Mapped[list[Job]] = relationship(back_populates="image_set", cascade="all, delete-orphan")


class SourceImage(Base):
    __tablename__ = "source_images"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    image_set_id: Mapped[str] = mapped_column(String(64), ForeignKey("image_sets.id"), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_format: Mapped[str | None] = mapped_column(String(64), nullable=True)
    camera_make: Mapped[str | None] = mapped_column(String(255), nullable=True)
    camera_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lens_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    iso: Mapped[float | None] = mapped_column(Float, nullable=True)
    aperture: Mapped[float | None] = mapped_column(Float, nullable=True)
    shutter_speed: Mapped[str | None] = mapped_column(String(64), nullable=True)
    exposure_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    exposure_bias: Mapped[float | None] = mapped_column(Float, nullable=True)
    focal_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    capture_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    black_level: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    white_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    cfa_pattern: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    color_matrix: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    camera_wb: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    measured_luminance: Mapped[float | None] = mapped_column(Float, nullable=True)
    exposure_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relative_exposure_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_reference: Mapped[bool] = mapped_column(Boolean, default=False)
    audit_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    audit_warnings: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    image_set: Mapped[ImageSet] = relationship(back_populates="source_images")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    image_set_id: Mapped[str] = mapped_column(String(64), ForeignKey("image_sets.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    pipeline_name: Mapped[str] = mapped_column(String(128), default=PIPELINE_NAME)
    pipeline_version: Mapped[str] = mapped_column(String(128), default=PIPELINE_VERSION)
    preset_name: Mapped[str] = mapped_column(String(128), default="real_estate_natural")
    preset_version: Mapped[str] = mapped_column(String(128), default="1.0.0")
    params: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    config_snapshot: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    output_artifact_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    image_set: Mapped[ImageSet] = relationship(back_populates="jobs")
    steps: Mapped[list[JobStep]] = relationship(back_populates="job", cascade="all, delete-orphan")
    artifacts: Mapped[list[Artifact]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobStep(Base):
    __tablename__ = "job_steps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.id"), nullable=False, index=True)
    step_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    metrics: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    artifacts: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    job: Mapped[Job] = relationship(back_populates="steps")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    job_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("jobs.id"), nullable=True, index=True)
    image_set_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("image_sets.id"), nullable=True, index=True)
    source_image_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("source_images.id"), nullable=True, index=True)
    artifact_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Any | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job: Mapped[Job | None] = relationship(back_populates="artifacts")


class Preset(Base):
    __tablename__ = "presets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(128), default="1.0.0")
    config: Mapped[Any] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PipelineVersion(Base):
    __tablename__ = "pipeline_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(128), nullable=False)
    git_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(128), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metadata_json: Mapped[Any | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    job_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("jobs.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


Index("ix_presets_name_version", Preset.name, Preset.version, unique=True)
Index("ix_pipeline_versions_name_version", PipelineVersion.name, PipelineVersion.version, unique=True)

