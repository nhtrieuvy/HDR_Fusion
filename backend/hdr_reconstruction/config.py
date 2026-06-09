from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def deep_update(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base without mutating either input."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_update(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: str | Path | None) -> dict[str, Any]:
    default_path = Path(__file__).parent / "configs" / "default.yaml"
    with default_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    if config_path:
        user_path = Path(config_path)
        if user_path.resolve() != default_path.resolve():
            with user_path.open("r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            config = deep_update(config, user_config)
    return config


def load_exposure_override(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    override_path = Path(path)
    if not override_path.exists():
        raise FileNotFoundError(f"Exposure override JSON not found: {override_path}")
    import json

    with override_path.open("r", encoding="utf-8") as f:
        return json.load(f)

