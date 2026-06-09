from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class NeutralBalanceResult:
    image: np.ndarray
    mask: np.ndarray
    metrics: dict[str, object]


def apply_neutral_balance(
    rgb: np.ndarray,
    strength: float = 0.32,
    max_gain: float = 1.14,
    exclude_mask: np.ndarray | None = None,
) -> NeutralBalanceResult:
    image = rgb.astype(np.float32)
    luma = 0.2126 * image[..., 0] + 0.7152 * image[..., 1] + 0.0722 * image[..., 2]
    maxc = np.max(image, axis=-1)
    minc = np.min(image, axis=-1)
    sat = (maxc - minc) / np.maximum(maxc, 1e-6)
    mask = (sat < 0.22) & (luma > 0.14) & (luma < 0.84)
    if exclude_mask is not None:
        mask &= ~np.asarray(exclude_mask).astype(bool)
    if np.count_nonzero(mask) < 128:
        return NeutralBalanceResult(
            image,
            mask,
            {
                "neutral_balance_applied": False,
                "neutral_surface_coverage": float(np.mean(mask)),
                "neutral_balance_warning": "insufficient_neutral_surfaces",
            },
        )
    samples = image[mask]
    low = np.percentile(samples, 5, axis=0)
    high = np.percentile(samples, 95, axis=0)
    robust = samples[np.all((samples >= low) & (samples <= high), axis=1)]
    if robust.shape[0] >= 128:
        samples = robust
    mean = np.median(samples, axis=0)
    target = float(np.median(mean))
    gains = np.clip(target / np.maximum(mean, 1e-6), 1.0 / max_gain, max_gain)
    applied = 1.0 + (gains - 1.0) * strength
    out = image * applied
    metrics = {
        "neutral_balance_applied": True,
        "neutral_surface_coverage": float(np.mean(mask)),
        "neutral_surface_rgb_mean": [float(v) for v in mean],
        "estimated_color_cast": [float(v - target) for v in mean],
        "neutral_gains": [float(v) for v in applied],
        "neutral_balance_strength": float(strength),
        "neutral_balance_max_gain": float(max_gain),
    }
    return NeutralBalanceResult(out.astype(np.float32), mask, metrics)
