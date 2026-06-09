from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from app.cv.hdr.weights import smooth_exposure_weights
from app.cv.raw.shape import raw_luminance_stack


@dataclass
class RawMergeResult:
    radiance: np.ndarray
    radiance_stack: np.ndarray
    weights: np.ndarray
    clipped_rejection_mask: np.ndarray
    underexposed_rejection_mask: np.ndarray
    metrics: dict[str, Any]


def merge_raw_domain_weighted_with_debug(
    stack: np.ndarray,
    exposure_ratios: np.ndarray,
    config: dict[str, Any] | None = None,
) -> RawMergeResult:
    cfg = config or {}
    low = float(cfg.get("low_threshold", 0.018))
    high = float(cfg.get("high_threshold", 0.945))
    eps = float(cfg.get("epsilon", 1e-8))
    ratios = np.maximum(exposure_ratios.astype(np.float32), 1e-8)
    raw = stack.astype(np.float32)
    luma = raw_luminance_stack(raw)
    ratio_shape = (raw.shape[0],) + (1,) * (raw.ndim - 1)
    radiance_stack = raw / ratios.reshape(ratio_shape)
    weights_2d = smooth_exposure_weights(luma, low, high)
    clipped = np.any(raw >= high, axis=-1) if raw.ndim == 4 else raw >= high
    under = luma <= low
    weights_2d = np.where(clipped | under, 0.0, weights_2d).astype(np.float32)
    weights_broadcast = weights_2d[..., None] if raw.ndim == 4 else weights_2d
    numerator = np.sum(weights_broadcast * radiance_stack, axis=0)
    denominator_2d = np.sum(weights_2d, axis=0)
    denominator = denominator_2d[..., None] if raw.ndim == 4 else denominator_2d
    fallback = np.median(radiance_stack, axis=0)
    radiance = np.where(denominator > eps, numerator / np.maximum(denominator, eps), fallback).astype(np.float32)
    radiance_luma = raw_luminance_stack(radiance[None, ...])[0] if radiance.ndim == 3 else radiance
    metrics = {
        "hdr_mosaic_min": float(np.min(radiance_luma)),
        "hdr_mosaic_max": float(np.max(radiance_luma)),
        "hdr_mosaic_median": float(np.median(radiance_luma)),
        "hdr_mosaic_p95": float(np.percentile(radiance_luma, 95)),
        "hdr_mosaic_p99": float(np.percentile(radiance_luma, 99)),
        "zero_confidence_percentage": float(np.mean(denominator_2d <= eps) * 100.0),
        "clipped_rejection_percentage": float(np.mean(np.any(clipped, axis=0)) * 100.0),
        "underexposed_rejection_percentage": float(np.mean(np.any(under, axis=0)) * 100.0),
        "raw_domain_merge_input_ndim": int(raw.ndim),
        "raw_domain_merge_channel_count": int(raw.shape[-1]) if raw.ndim == 4 else 1,
    }
    return RawMergeResult(radiance, radiance_stack, weights_2d, np.any(clipped, axis=0), np.any(under, axis=0), metrics)
