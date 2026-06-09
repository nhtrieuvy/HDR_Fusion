from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PresetRead(BaseModel):
    name: str
    version: str
    config: dict[str, Any]

