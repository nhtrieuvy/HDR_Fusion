from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.cv.finishing.aces import aces_filmic


@dataclass
class ToneMapResult:
    image: np.ndarray
    metrics: dict[str, float]
    debug: dict[str, np.ndarray]


def tone_map_interior(
    rgb: np.ndarray,
    source_mask: np.ndarray | None = None,
    exposure: float = 1.0,
    shadow_lift: float = 0.045,
    saturation: float = 1.03,
    final_p99_target: float = 0.92,
) -> ToneMapResult:
    image = np.maximum(rgb.astype(np.float32), 0.0)
    luma = 0.2126 * image[..., 0] + 0.7152 * image[..., 1] + 0.0722 * image[..., 2]
    source = source_mask if source_mask is not None else np.zeros(luma.shape, dtype=bool)
    meter = (luma > np.percentile(luma, 18)) & (luma < np.percentile(luma, 82)) & ~source
    target_median = 0.34
    current = float(np.median(luma[meter])) if np.any(meter) else float(np.median(luma))
    auto = np.clip(target_median / max(current, 1e-6), 0.55, 8.0)
    scaled = image * exposure * auto
    before = scaled.copy()
    p99 = float(np.percentile(0.2126 * scaled[..., 0] + 0.7152 * scaled[..., 1] + 0.0722 * scaled[..., 2], 99))
    if p99 > final_p99_target:
        scaled *= final_p99_target / max(p99, 1e-6)
    mapped = aces_filmic(scaled)
    luma_mapped = 0.2126 * mapped[..., 0] + 0.7152 * mapped[..., 1] + 0.0722 * mapped[..., 2]
    mapped = mapped + shadow_lift * np.clip(0.35 - luma_mapped, 0.0, 0.35)[..., None]
    gray = luma_mapped[..., None]
    mapped = gray + (mapped - gray) * saturation
    mapped = np.clip(mapped, 0.0, 1.0)
    out = (np.clip(mapped, 0.0, 1.0) ** (1 / 2.2) * 255.0).astype(np.uint8)
    final_luma = 0.2126 * mapped[..., 0] + 0.7152 * mapped[..., 1] + 0.0722 * mapped[..., 2]
    danger = (final_luma > 0.96) | source
    debug = {
        "metering_mask": meter.astype(np.float32),
        "highlight_danger_mask": danger.astype(np.float32),
        "tonemap_before_auto_exposure": np.clip(before / max(float(np.max(before)), 1e-6), 0.0, 1.0),
        "tonemap_after_auto_exposure": mapped.astype(np.float32),
    }
    metrics = {
        "auto_exposure_scale_raw": float(auto),
        "auto_exposure_scale_clamped": float(auto),
        "metering_mask_coverage": float(np.mean(meter)),
        "final_median_luminance": float(np.median(final_luma)),
        "final_p95_luminance": float(np.percentile(final_luma, 95)),
        "final_p99_luminance": float(np.percentile(final_luma, 99)),
        "near_clip_percentage": float(np.mean(final_luma > 0.98) * 100.0),
        "highlight_clip_percentage": float(np.mean(final_luma >= 0.999) * 100.0),
        "shadow_percentage": float(np.mean(final_luma < 0.05) * 100.0),
    }
    return ToneMapResult(out, metrics, debug)

