from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from app.cv.hdr.typed_source_masks import TypedSourceMaskResult
from app.cv.raw.shape import expand_spatial_mask


@dataclass
class SourceCompositeResult:
    radiance: np.ndarray
    amount: np.ndarray
    metrics: dict[str, Any]
    warnings: list[str]


def composite_valid_sources(
    base_radiance: np.ndarray,
    radiance_stack: np.ndarray,
    masks: TypedSourceMaskResult,
    config: dict[str, Any] | None = None,
    dark_index: int = 0,
) -> SourceCompositeResult:
    cfg = config or {}
    strength = float(cfg.get("source_compositor_strength", 0.90))
    source_sigma = float(cfg.get("source_feather_sigma", 2.0))
    window_strength = float(cfg.get("window_compositor_strength", strength))
    window_sigma = float(cfg.get("window_feather_sigma", max(1.0, source_sigma * 0.7)))
    source_mask = masks.valid_dark_source_detail.astype(np.float32)
    window_mask = masks.window_recoverable_detail.astype(np.float32)
    if source_mask.max() <= 0 and window_mask.max() <= 0:
        return SourceCompositeResult(
            base_radiance,
            np.zeros_like(base_radiance, dtype=np.float32),
            {
                "source_compositor_coverage": 0.0,
                "source_compositor_mean_amount": 0.0,
                "window_recovery_coverage": 0.0,
                "window_recovery_mean_amount": 0.0,
                "valid_source_detail_found": False,
                "window_detail_recoverable": False,
                "window_unrecoverable_coverage": float(np.mean(masks.window_unrecoverable)),
            },
            [*masks.warnings, "no_valid_dark_source_detail_for_compositor"],
        )
    best = np.min(radiance_stack, axis=0).astype(np.float32)
    darkest = radiance_stack[int(np.clip(dark_index, 0, radiance_stack.shape[0] - 1))].astype(np.float32)
    target = best.copy()
    window_broadcast = expand_spatial_mask(masks.window_recoverable_detail, target)
    target = np.where(window_broadcast, darkest, target)

    source_feather = cv2.GaussianBlur(source_mask, (0, 0), source_sigma)
    source_feather = np.clip(source_feather * strength, 0.0, 1.0).astype(np.float32)
    window_feather = cv2.GaussianBlur(window_mask, (0, 0), window_sigma)
    window_feather = np.clip(window_feather * window_strength, 0.0, 1.0).astype(np.float32)
    feather = np.maximum(source_feather, window_feather)
    feather_broadcast = expand_spatial_mask(feather > 0, base_radiance).astype(np.float32) * feather[..., None] if base_radiance.ndim == 3 else feather
    out = base_radiance * (1.0 - feather_broadcast) + target * feather_broadcast
    metrics = {
        "source_compositor_coverage": float(np.mean(feather > 0.01)),
        "source_compositor_mean_amount": float(np.mean(feather)),
        "window_recovery_coverage": float(np.mean(window_feather > 0.01)),
        "window_recovery_mean_amount": float(np.mean(window_feather)),
        "window_detail_recoverable": bool(window_mask.max() > 0),
        "window_unrecoverable_coverage": float(np.mean(masks.window_unrecoverable)),
        "valid_source_detail_found": True,
    }
    return SourceCompositeResult(out.astype(np.float32), feather, metrics, masks.warnings)
