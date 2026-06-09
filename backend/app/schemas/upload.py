from __future__ import annotations

from pydantic import BaseModel


class PresignUploadRequest(BaseModel):
    user_id: str
    project_id: str
    image_set_id: str
    source_image_id: str
    filename: str
    content_type: str | None = None
    file_size: int | None = None
    purpose: str | None = "source_raw"


class PresignUploadResponse(BaseModel):
    storage_key: str
    upload_url: str
    method: str
    headers: dict[str, str] = {}
    asset_id: str | None = None

