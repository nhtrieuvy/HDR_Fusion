from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from app.cv.hdr.typed_source_masks import TypedSourceMaskResult
from app.cv.raw.shape import expand_spatial_mask


@dataclass
class RadianceSafetyResult:
    amaze_input: np.ndarray
    input_scale: float
    technical_clip_mask: np.ndarray
    near_clip_mask: np.ndarray
    metrics: dict[str, Any]


def analyze_amaze_input_scale(raw_radiance: np.ndarray, input_percentile: float, target_white: float) -> RadianceSafetyResult:
    return prepare_amaze_input_with_safety(
        raw_radiance,
        masks=None,
        input_percentile=input_percentile,
        target_white=target_white,
    )


def prepare_amaze_input_with_safety(
    raw_radiance: np.ndarray,
    masks: TypedSourceMaskResult | None = None,
    input_percentile: float = 99.9,
    target_white: float = 0.84,
    shoulder_strength: float = 0.55,
    source_ceiling_ratio: float = 0.92,
) -> RadianceSafetyResult:
    radiance = np.maximum(raw_radiance.astype(np.float32), 0.0)
    scale_base = float(np.percentile(radiance[np.isfinite(radiance)], input_percentile))
    scale = target_white / max(scale_base, 1e-8)
    scaled = radiance * scale
    source_mask = masks.source_and_bloom if masks is not None else np.zeros(radiance.shape, dtype=bool)
    if masks is not None:
        source_mask = expand_spatial_mask(source_mask, radiance)
    ceiling = target_white * source_ceiling_ratio
    over = scaled > ceiling
    compressed = scaled.copy()
    if np.any(over):
        excess = scaled[over] - ceiling
        compressed[over] = ceiling + excess / (1.0 + shoulder_strength * excess / max(ceiling, 1e-8))
    non_source_clip = (compressed > target_white) & ~source_mask
    compressed = np.where(non_source_clip, target_white, compressed)
    technical_per_channel = compressed >= target_white
    near_per_channel = compressed >= target_white * 0.96
    technical = np.any(technical_per_channel, axis=-1) if compressed.ndim == 3 else technical_per_channel
    near = np.any(near_per_channel, axis=-1) if compressed.ndim == 3 else near_per_channel
    metrics = {
        "amaze_input_percentile": input_percentile,
        "amaze_input_white": target_white,
        "amaze_input_scale": scale,
        "amaze_input_preclip_percentage": float(np.mean(scaled >= target_white) * 100.0),
        "amaze_input_technical_clip_percentage": float(np.mean(technical) * 100.0),
        "amaze_input_near_clip_percentage": float(np.mean(near) * 100.0),
        "source_aware_radiance_safety": masks is not None,
    }
    return RadianceSafetyResult(compressed.astype(np.float32), scale, technical, near, metrics)
