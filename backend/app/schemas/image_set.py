from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ImageSetCreate(BaseModel):
    project_id: str
    name: str | None = None
    capture_group: str | None = None


class ImageSetRead(BaseModel):
    id: str
    project_id: str
    name: str | None
    capture_group: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

