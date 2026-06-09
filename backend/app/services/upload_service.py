from __future__ import annotations

from app.schemas.upload import PresignUploadRequest, PresignUploadResponse
from app.services.storage_service import StorageService


def create_presigned_upload(payload: PresignUploadRequest) -> PresignUploadResponse:
    storage = StorageService()
    key = storage.original_key(
        payload.user_id,
        payload.project_id,
        payload.image_set_id,
        payload.source_image_id,
        payload.filename,
    )
    return PresignUploadResponse(
        storage_key=key,
        upload_url=storage.presign_put(key, payload.content_type),
        method="PUT",
        headers={"Content-Type": payload.content_type} if payload.content_type else {},
        asset_id=payload.source_image_id,
    )

