from __future__ import annotations

from fastapi import APIRouter

from app.core.versions import API_VERSION, PIPELINE_NAME, PIPELINE_VERSION

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    return {
        "status": "ok",
        "api_version": API_VERSION,
        "pipeline_name": PIPELINE_NAME,
        "pipeline_version": PIPELINE_VERSION,
    }

