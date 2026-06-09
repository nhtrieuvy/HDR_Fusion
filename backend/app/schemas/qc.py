from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class QCReport(BaseModel):
    status: str
    selected_candidate: str | None = None
    recommended_action: str | None = None
    warnings: list[str] = []
    metrics: dict[str, Any] = {}

