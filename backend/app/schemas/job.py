from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


JobStatus = Literal["queued", "running", "failed", "completed", "qc_failed", "manual_review", "cancelled"]


class JobCreate(BaseModel):
    image_set_id: str
    pipeline_name: str | None = "raw_hdr_fusion"
    preset_name: str = "real_estate_natural"
    mode: str | None = "quality"
    params: dict[str, Any] | None = None


class RetryJobRequest(BaseModel):
    strategy: str = "same_params"
    preset_name: str | None = None


class ReenhanceJobRequest(BaseModel):
    preset_name: str = "real_estate_natural"
    mode: str | None = "quality"
    params: dict[str, Any] | None = None


class JobRead(BaseModel):
    id: str
    image_set_id: str
    status: str
    progress: float
    pipeline_name: str
    pipeline_version: str
    preset_name: str
    preset_version: str
    params: Any | None
    config_snapshot: Any | None
    output_artifact_id: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class JobStepRead(BaseModel):
    id: str
    job_id: str
    step_name: str
    status: str
    progress: float
    metrics: Any | None
    warnings: Any | None
    artifacts: Any | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}

