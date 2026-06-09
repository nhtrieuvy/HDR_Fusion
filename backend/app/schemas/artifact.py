from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ArtifactCreate(BaseModel):
    job_id: str | None = None
    image_set_id: str | None = None
    source_image_id: str | None = None
    artifact_type: str
    storage_key: str
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    file_size: int | None = None
    metadata: dict[str, Any] | None = None


class ArtifactRead(BaseModel):
    id: str
    job_id: str | None
    image_set_id: str | None
    source_image_id: str | None
    artifact_type: str
    storage_key: str
    mime_type: str | None
    width: int | None
    height: int | None
    file_size: int | None
    metadata_json: Any | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactAccess(BaseModel):
    artifact: ArtifactRead
    url: str
    method: str = "GET"

