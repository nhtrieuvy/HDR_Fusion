from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import http_bad_request, http_not_found
from app.db.session import get_db
from app.schemas.image_set import ImageSetCreate, ImageSetRead
from app.schemas.source_image import SourceImageCreate, SourceImageRead
from app.services.image_set_service import create_image_set, get_image_set, register_source_image

router = APIRouter(prefix="/image-sets", tags=["image-sets"])


@router.post("", response_model=ImageSetRead)
def post_image_set(payload: ImageSetCreate, db: Session = Depends(get_db)):
    return create_image_set(db, payload)


@router.get("/{image_set_id}", response_model=ImageSetRead)
def get_one_image_set(image_set_id: str, db: Session = Depends(get_db)):
    image_set = get_image_set(db, image_set_id)
    if image_set is None:
        raise http_not_found("Image set not found")
    return image_set


@router.post("/{image_set_id}/source-images", response_model=SourceImageRead)
def post_source_image(image_set_id: str, payload: SourceImageCreate, db: Session = Depends(get_db)):
    if image_set_id != payload.image_set_id:
        raise http_bad_request("image_set_id in path and body must match")
    if get_image_set(db, image_set_id) is None:
        raise http_not_found("Image set not found")
    return register_source_image(db, payload)

