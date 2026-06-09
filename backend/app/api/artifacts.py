from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.errors import http_not_found
from app.core.config import settings
from app.db.models import Artifact
from app.db.session import get_db
from app.schemas.artifact import ArtifactAccess
from app.services.storage_service import StorageService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{artifact_id}", response_model=ArtifactAccess)
def get_artifact_access(artifact_id: str, db: Session = Depends(get_db)):
    artifact = db.get(Artifact, artifact_id)
    if artifact is None:
        raise http_not_found("Artifact not found")
    return ArtifactAccess(artifact=artifact, url=f"{settings.api_prefix}/artifacts/{artifact.id}/content")


@router.get("/{artifact_id}/content")
def get_artifact_content(artifact_id: str, download: bool = False, db: Session = Depends(get_db)):
    artifact = db.get(Artifact, artifact_id)
    if artifact is None:
        raise http_not_found("Artifact not found")
    storage = StorageService()
    media_type = artifact.mime_type or "application/octet-stream"
    filename = artifact.storage_key.rsplit("/", 1)[-1]
    if storage.backend == "local":
        path = storage.local_path(artifact.storage_key)
        if not path.exists() or not path.is_file():
            raise http_not_found("Artifact file not found")
        return FileResponse(path, media_type=media_type, filename=path.name, content_disposition_type="attachment" if download else "inline")

    stream = storage.open_stream(artifact.storage_key)
    disposition = "attachment" if download else "inline"
    return StreamingResponse(
        stream,
        media_type=media_type,
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )
