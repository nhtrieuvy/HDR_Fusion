from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SourceImageCreate(BaseModel):
    image_set_id: str
    storage_key: str
    original_filename: str
    mime_type: str | None = None
    file_size: int | None = None
    metadata: dict[str, Any] | None = None


class SourceImageRead(BaseModel):
    id: str
    image_set_id: str
    storage_key: str
    original_filename: str
    mime_type: str | None
    file_size: int | None
    raw_format: str | None
    camera_make: str | None
    camera_model: str | None
    lens_model: str | None
    width: int | None
    height: int | None
    iso: float | None
    aperture: float | None
    shutter_speed: str | None
    exposure_time: float | None
    exposure_bias: float | None
    focal_length: float | None
    capture_time: datetime | None
    black_level: Any | None
    white_level: float | None
    cfa_pattern: Any | None
    color_matrix: Any | None
    camera_wb: Any | None
    measured_luminance: float | None
    exposure_order: int | None
    relative_exposure_ratio: float | None
    is_reference: bool
    audit_status: str
    audit_warnings: Any | None
    created_at: datetime

    model_config = {"from_attributes": True}

