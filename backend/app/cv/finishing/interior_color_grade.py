from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class InteriorColorGradeResult:
    image: np.ndarray
    vibrance_amount: np.ndarray
    wood_mask: np.ndarray
    source_protection: np.ndarray
    neutral_protection: np.ndarray
    metrics: dict[str, float]


def apply_interior_color_grade(
    rgb: np.ndarray,
    source_mask: np.ndarray | None = None,
    neutral_mask: np.ndarray | None = None,
    vibrance_strength: float = 0.22,
    wood_warmth_strength: float = 0.06,
    clarity_strength: float = 0.07,
    source_protection_strength: float = 0.96,
    neutral_protection_strength: float = 0.72,
) -> InteriorColorGradeResult:
    image = np.maximum(rgb.astype(np.float32), 0.0)
    luma = _luminance(image)
    sat = _saturation(image)
    source = np.asarray(source_mask).astype(bool) if source_mask is not None else np.zeros(luma.shape, dtype=bool)
    neutral = np.asarray(neutral_mask).astype(bool) if neutral_mask is not None else np.zeros(luma.shape, dtype=bool)

    source_core = source.astype(np.float32) * source_protection_strength
    source_protection = cv2.GaussianBlur(source.astype(np.float32), (0, 0), 5.0)
    source_protection = np.maximum(source_core, np.clip(source_protection * source_protection_strength, 0.0, 1.0))
    neutral_protection = neutral.astype(np.float32) * neutral_protection_strength
    protect = np.maximum(source_protection, neutral_protection)

    midtone = _smooth_range(luma, 0.08, 0.22) * (1.0 - _smooth_range(luma, 0.86, 0.98))
    low_sat_bias = np.clip(1.0 - sat / 0.58, 0.0, 1.0)
    vibrance_amount = np.clip(vibrance_strength * low_sat_bias * midtone * (1.0 - protect), 0.0, 0.35)
    graded = _apply_saturation(image, 1.0 + vibrance_amount)

    wood_mask = _wood_like_mask(graded, luma, sat) & ~source & ~neutral
    wood_amount = wood_mask.astype(np.float32) * wood_warmth_strength * (1.0 - protect)
    warmth_gains = np.stack(
        [
            1.0 + 0.85 * wood_amount,
            1.0 + 0.20 * wood_amount,
            1.0 - 0.55 * wood_amount,
        ],
        axis=-1,
    )
    graded = graded * warmth_gains

    if clarity_strength > 0:
        graded = _apply_local_clarity(graded, source, clarity_strength)

    graded = np.clip(graded, 0.0, None)
    metrics = {
        "interior_color_grade_vibrance_strength": float(vibrance_strength),
        "interior_color_grade_mean_vibrance_amount": float(np.mean(vibrance_amount)),
        "interior_color_grade_vibrance_coverage": float(np.mean(vibrance_amount > 0.01)),
        "interior_color_grade_wood_warmth_strength": float(wood_warmth_strength),
        "interior_color_grade_wood_coverage": float(np.mean(wood_mask)),
        "interior_color_grade_clarity_strength": float(clarity_strength),
        "interior_color_grade_source_protection_coverage": float(np.mean(source_protection > 0.05)),
        "interior_color_grade_neutral_protection_coverage": float(np.mean(neutral_protection > 0.05)),
        "colorfulness_before": _colorfulness(image),
        "colorfulness_after": _colorfulness(graded),
    }
    return InteriorColorGradeResult(
        graded.astype(np.float32),
        vibrance_amount.astype(np.float32),
        wood_mask,
        source_protection.astype(np.float32),
        neutral_protection.astype(np.float32),
        metrics,
    )


def _luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def _saturation(rgb: np.ndarray) -> np.ndarray:
    maxc = np.max(rgb, axis=-1)
    minc = np.min(rgb, axis=-1)
    return (maxc - minc) / np.maximum(maxc, 1e-6)


def _apply_saturation(rgb: np.ndarray, factor: np.ndarray) -> np.ndarray:
    luma = _luminance(rgb)[..., None]
    return luma + (rgb - luma) * factor[..., None]


def _wood_like_mask(rgb: np.ndarray, luma: np.ndarray, sat: np.ndarray) -> np.ndarray:
    red = rgb[..., 0]
    green = rgb[..., 1]
    blue = rgb[..., 2]
    return (
        (luma > 0.10)
        & (luma < 0.82)
        & (sat > 0.10)
        & (red > blue * 1.08)
        & (green > blue * 0.82)
        & (red < green * 1.75)
    )


def _apply_local_clarity(rgb: np.ndarray, source_mask: np.ndarray, strength: float) -> np.ndarray:
    luma = _luminance(rgb)
    base = cv2.GaussianBlur(luma, (0, 0), 5.0)
    detail = np.clip(luma - base, -0.12, 0.12)
    midtone = _smooth_range(luma, 0.10, 0.28) * (1.0 - _smooth_range(luma, 0.82, 0.96))
    source_protection = cv2.GaussianBlur(source_mask.astype(np.float32), (0, 0), 7.0)
    amount = strength * midtone * (1.0 - np.clip(source_protection, 0.0, 1.0))
    gain = 1.0 + np.clip(detail * amount / np.maximum(luma, 0.08), -0.08, 0.10)
    return rgb * gain[..., None]


def _smooth_range(values: np.ndarray, low: float, high: float) -> np.ndarray:
    x = np.clip((values - low) / max(high - low, 1e-6), 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _colorfulness(rgb: np.ndarray) -> float:
    clipped = np.clip(rgb.astype(np.float32), 0.0, 1.0)
    rg = clipped[..., 0] - clipped[..., 1]
    yb = 0.5 * (clipped[..., 0] + clipped[..., 1]) - clipped[..., 2]
    std = np.sqrt(float(np.var(rg) + np.var(yb)))
    mean = np.sqrt(float(np.mean(rg) ** 2 + np.mean(yb) ** 2))
    return float(std + 0.30 * mean)
