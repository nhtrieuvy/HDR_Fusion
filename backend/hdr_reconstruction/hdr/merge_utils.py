from __future__ import annotations

from typing import Any

import numpy as np

from hdr_reconstruction.hdr.base import HDRResult
from hdr_reconstruction.tonemapping.tonemap import tone_map_with_metadata
from hdr_reconstruction.utils.image_utils import hdr_statistics, sanitize_float_image


def luminance(rgb: np.ndarray) -> np.ndarray:
    return (
        0.2126 * rgb[..., 0]
        + 0.7152 * rgb[..., 1]
        + 0.0722 * rgb[..., 2]
    ).astype(np.float32)


def triangular_weights(values: np.ndarray, low: float, high: float) -> np.ndarray:
    data = np.clip(values, 0.0, 1.0).astype(np.float32, copy=False)
    midpoint = 0.5 * (low + high)
    weights = np.zeros_like(data, dtype=np.float32)
    rising = (data >= low) & (data <= midpoint)
    falling = (data > midpoint) & (data <= high)
    weights[rising] = (data[rising] - low) / max(midpoint - low, 1e-8)
    weights[falling] = (high - data[falling]) / max(high - midpoint, 1e-8)
    return np.clip(weights, 0.0, 1.0)


def finalize_hdr_result(result: HDRResult, hdr: np.ndarray, config: dict[str, Any]) -> None:
    clean = sanitize_float_image(hdr).astype(np.float32)
    result.hdr_radiance_map = clean
    preview = tone_map_with_metadata(clean, config)
    result.preview_png = preview.image
    result.metadata.update(hdr_statistics(clean))
    result.metadata["tone_mapping"] = preview.metadata


def init_accumulators(shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    numerator = np.zeros(shape, dtype=np.float32)
    denominator = np.zeros(shape, dtype=np.float32)
    fallback_sum = np.zeros(shape, dtype=np.float32)
    return numerator, denominator, fallback_sum


def finalize_weighted_average(
    numerator: np.ndarray,
    denominator: np.ndarray,
    fallback_sum: np.ndarray,
    count: int,
    eps: float,
) -> np.ndarray:
    fallback = fallback_sum / max(count, 1)
    return np.where(denominator > eps, numerator / np.maximum(denominator, eps), fallback).astype(np.float32)
