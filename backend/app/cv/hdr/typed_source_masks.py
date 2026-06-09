from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from app.cv.raw.shape import raw_luminance


@dataclass
class TypedSourceMaskResult:
    masks: dict[str, np.ndarray]
    source_core: np.ndarray
    source_and_bloom: np.ndarray
    valid_dark_source_detail: np.ndarray
    window_core: np.ndarray
    window_recoverable_detail: np.ndarray
    window_unrecoverable: np.ndarray
    unrecoverable_clipped_source: np.ndarray
    metrics: dict[str, Any]
    warnings: list[str]


def analyze_typed_source_masks(
    stack: np.ndarray,
    exposure_order: list[int],
    reference_index: int,
    config: dict[str, Any] | None = None,
) -> TypedSourceMaskResult:
    cfg = config or {}
    strictness = float(cfg.get("source_mask_strictness", 0.78))
    window_detail_min_std = float(cfg.get("window_detail_min_std", 0.018))
    window_detail_min_fraction = float(cfg.get("window_detail_min_fraction", 0.03))
    dark = raw_luminance(stack[int(exposure_order[0])])
    ref = raw_luminance(stack[reference_index])
    bright_ref = ref > max(0.82, strictness)
    very_bright_ref = ref > max(0.92, strictness + 0.08)
    dark_clipped = dark > 0.985
    dark_detail = (dark > 0.08) & (dark < 0.88)

    compact_source = _remove_large_low_confidence_regions(very_bright_ref, max_area_fraction=0.08)
    light_bulb_core = _small_components(compact_source, max_area_fraction=0.012)
    window_candidates = bright_ref & ~light_bulb_core
    window_core = _window_components_with_dark_detail(
        window_candidates,
        dark,
        min_area_fraction=0.0008,
        max_area_fraction=0.30,
        min_std=window_detail_min_std,
        min_detail_fraction=window_detail_min_fraction,
    )
    if not np.any(window_core):
        window_core = _window_components_with_dark_detail(
            very_bright_ref & ~light_bulb_core,
            dark,
            min_area_fraction=0.0004,
            max_area_fraction=0.30,
            min_std=window_detail_min_std * 0.75,
            min_detail_fraction=window_detail_min_fraction * 0.50,
        )
    light_bloom = _dilate(light_bulb_core, 17) & bright_ref & ~light_bulb_core
    window_frame_edge = _edge_ring(window_core, 7)
    specular_reflection = _small_components((ref > 0.88) & (dark < 0.96), max_area_fraction=0.006)
    floor_glare = specular_reflection & _lower_half(ref)
    wall_near_source = _dilate(window_core | light_bulb_core, 31) & (ref > 0.65) & ~(window_core | light_bulb_core)
    ceiling_near_source = wall_near_source & _upper_half(ref)
    false_positive = _large_components(bright_ref, min_area_fraction=0.12)
    source_core = window_core | (light_bulb_core & ~false_positive)
    source_and_bloom = source_core | light_bloom | window_frame_edge
    window_recoverable = window_core & dark_detail & ~dark_clipped
    window_unrecoverable = window_core & dark_clipped
    valid_detail = (source_and_bloom & dark_detail & ~dark_clipped) | window_recoverable
    unrecoverable = source_core & dark_clipped

    masks = {
        "window_core": window_core,
        "window_recoverable_detail": window_recoverable,
        "window_unrecoverable": window_unrecoverable,
        "window_frame_edge": window_frame_edge,
        "light_bulb_core": light_bulb_core,
        "light_bloom": light_bloom,
        "specular_reflection": specular_reflection,
        "floor_glare": floor_glare,
        "wall_near_source": wall_near_source,
        "ceiling_near_source": ceiling_near_source,
        "countertop_or_wall_false_positive": false_positive,
        "unrecoverable_clipped_source": unrecoverable,
        "valid_dark_source_detail": valid_detail,
    }
    metrics = {f"{name}_coverage": float(mask.mean()) for name, mask in masks.items()}
    metrics.update(
        {
            "source_core_coverage": float(source_core.mean()),
            "source_and_bloom_coverage": float(source_and_bloom.mean()),
            "valid_dark_source_detail_coverage": float(valid_detail.mean()),
            "window_recoverable_detail_fraction": _safe_fraction(window_recoverable, window_core),
            "window_exterior_detail_confidence": _safe_fraction(window_recoverable, window_core),
            "unrecoverable_source_coverage": float(unrecoverable.mean()),
        }
    )
    warnings = []
    if metrics["countertop_or_wall_false_positive_coverage"] > 0.05:
        warnings.append("broad_bright_surface_rejected_from_source_core")
    if metrics["unrecoverable_source_coverage"] > 0.001:
        warnings.append("darkest_raw_has_true_source_clipping")
    if metrics["window_core_coverage"] > 0.0 and metrics["window_exterior_detail_confidence"] < 0.03:
        warnings.append("window_detail_unrecoverable_in_darkest_raw")
    return TypedSourceMaskResult(
        masks,
        source_core,
        source_and_bloom,
        valid_detail,
        window_core,
        window_recoverable,
        window_unrecoverable,
        unrecoverable,
        metrics,
        warnings,
    )


def _dilate(mask: np.ndarray, size: int) -> np.ndarray:
    kernel = np.ones((size, size), np.uint8)
    return cv2.dilate(mask.astype(np.uint8), kernel).astype(bool)


def _edge_ring(mask: np.ndarray, size: int) -> np.ndarray:
    return _dilate(mask, size) & ~mask


def _upper_half(image: np.ndarray) -> np.ndarray:
    mask = np.zeros(image.shape, dtype=bool)
    mask[: image.shape[0] // 2, :] = True
    return mask


def _lower_half(image: np.ndarray) -> np.ndarray:
    mask = np.zeros(image.shape, dtype=bool)
    mask[image.shape[0] // 2 :, :] = True
    return mask


def _small_components(mask: np.ndarray, max_area_fraction: float) -> np.ndarray:
    mask_u8 = _as_connected_components_mask(mask)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask_u8, connectivity=8, ltype=cv2.CV_32S)
    out = np.zeros(mask.shape, dtype=bool)
    max_area = max(mask.size * max_area_fraction, 64.0)
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] <= max_area:
            out |= labels == label
    return out


def _large_components(mask: np.ndarray, min_area_fraction: float) -> np.ndarray:
    mask_u8 = _as_connected_components_mask(mask)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask_u8, connectivity=8, ltype=cv2.CV_32S)
    out = np.zeros(mask.shape, dtype=bool)
    min_area = mask.size * min_area_fraction
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] >= min_area:
            out |= labels == label
    return out


def _remove_large_low_confidence_regions(mask: np.ndarray, max_area_fraction: float) -> np.ndarray:
    return mask & ~_large_components(mask, max_area_fraction)


def _window_components_with_dark_detail(
    mask: np.ndarray,
    dark_luma: np.ndarray,
    *,
    min_area_fraction: float,
    max_area_fraction: float,
    min_std: float,
    min_detail_fraction: float,
) -> np.ndarray:
    mask_u8 = _as_connected_components_mask(mask)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask_u8, connectivity=8, ltype=cv2.CV_32S)
    out = np.zeros(mask.shape, dtype=bool)
    min_area = mask.size * min_area_fraction
    max_area = mask.size * max_area_fraction
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < min_area or area > max_area:
            continue
        region = labels == label
        dark_values = dark_luma[region]
        if dark_values.size == 0:
            continue
        detail_fraction = float(np.mean((dark_values > 0.05) & (dark_values < 0.96)))
        if float(np.std(dark_values)) >= min_std and detail_fraction >= min_detail_fraction:
            out |= region
    return out


def _safe_fraction(numerator: np.ndarray, denominator: np.ndarray) -> float:
    denominator_count = int(np.count_nonzero(denominator))
    if denominator_count == 0:
        return 0.0
    return float(np.count_nonzero(numerator & denominator) / denominator_count)


def _as_connected_components_mask(mask: np.ndarray) -> np.ndarray:
    mask_bool = np.asarray(mask).astype(bool)
    if mask_bool.ndim != 2:
        raise ValueError(f"connected components mask must be 2D, got shape={mask_bool.shape}")
    return mask_bool.astype(np.uint8)
