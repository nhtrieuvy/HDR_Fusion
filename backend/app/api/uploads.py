from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.schemas.upload import PresignUploadRequest, PresignUploadResponse
from app.services.storage_service import StorageService
from app.services.upload_service import create_presigned_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/presign", response_model=PresignUploadResponse)
def presign_upload(payload: PresignUploadRequest):
    return create_presigned_upload(payload)


@router.post("/direct", response_model=PresignUploadResponse)
def direct_upload(
    user_id: str,
    project_id: str,
    image_set_id: str,
    source_image_id: str,
    file: UploadFile = File(...),
):
    storage = StorageService()
    key = storage.original_key(user_id, project_id, image_set_id, source_image_id, file.filename or "source.raw")
    size = storage.put_stream(file.file, key, file.content_type)
    if size > settings.direct_upload_max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds upload limit")
    return PresignUploadResponse(storage_key=key, upload_url=storage.presign_get(key), method="LOCAL")

