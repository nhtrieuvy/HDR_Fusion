from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


PRESET_ROOT = Path(__file__).resolve().parents[2] / "presets"


def load_preset(name: str) -> dict[str, Any]:
    path = PRESET_ROOT / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Preset not found: {name}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("name", name)
    data.setdefault("version", "1.0.0")
    return data


def merge_params(config: dict[str, Any], params: dict[str, Any] | None) -> dict[str, Any]:
    merged = deepcopy(config)
    if params:
        merged.setdefault("runtime_params", {}).update(params)
    return merged

