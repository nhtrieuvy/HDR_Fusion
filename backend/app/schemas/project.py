from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    user_id: str | None = None


class ProjectRead(BaseModel):
    id: str
    user_id: str | None
    name: str
    description: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

