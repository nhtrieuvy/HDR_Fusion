from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class NormalizedRaw:
    mosaic: np.ndarray
    metrics: dict[str, Any]
    clip_mask: np.ndarray


def normalize_raw_mosaic(raw_image: np.ndarray, black_level: Any | None, white_level: float | None) -> NormalizedRaw:
    raw = raw_image.astype(np.float32, copy=False)
    black = _black_level_for_shape(black_level, raw.shape)
    white = float(white_level or np.nanmax(raw) or 1.0)
    denom = np.maximum(white - black, 1.0)
    corrected = (raw - black) / denom
    pre_clip_high = corrected >= 1.0
    normalized = np.clip(corrected, 0.0, 1.0).astype(np.float32)
    metrics = {
        "raw_min": float(np.nanmin(normalized)),
        "raw_max": float(np.nanmax(normalized)),
        "raw_median": float(np.nanmedian(normalized)),
        "raw_p95": float(np.nanpercentile(normalized, 95)),
        "raw_p99": float(np.nanpercentile(normalized, 99)),
        "black_level_used": _json_black_level(black),
        "white_level_used": white,
        "raw_clip_percentage": float(np.mean(pre_clip_high) * 100.0),
    }
    return NormalizedRaw(normalized, metrics, pre_clip_high)


def _black_level_for_shape(black_level: Any | None, shape: tuple[int, ...]) -> np.ndarray | float:
    if black_level is None:
        return 0.0
    try:
        values = np.asarray(black_level, dtype=np.float32)
        if len(shape) == 3 and values.ndim == 1 and values.size >= shape[-1]:
            return values[: shape[-1]].reshape((1, 1, shape[-1]))
        return float(np.mean(values))
    except Exception:
        return float(black_level)


def _json_black_level(black: np.ndarray | float) -> float | list[float]:
    if isinstance(black, np.ndarray):
        return [float(v) for v in black.reshape(-1)]
    return float(black)
