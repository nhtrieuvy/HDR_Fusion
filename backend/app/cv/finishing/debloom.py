from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class DebloomResult:
    image: np.ndarray
    amount: np.ndarray
    metrics: dict[str, float]


def apply_linear_debloom(rgb: np.ndarray, source_mask: np.ndarray, strength: float = 0.25) -> DebloomResult:
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    bloom = cv2.GaussianBlur(source_mask.astype(np.float32), (0, 0), 13.0)
    amount = np.clip(bloom * strength * np.clip(luma - 0.45, 0.0, 1.0), 0.0, 0.55)
    out = rgb - amount[..., None] * cv2.GaussianBlur(rgb, (0, 0), 5.0)
    out = np.maximum(out, 0.0)
    metrics = {"linear_debloom_coverage": float(np.mean(amount > 0.01)), "linear_debloom_mean_amount": float(np.mean(amount))}
    return DebloomResult(out.astype(np.float32), amount.astype(np.float32), metrics)

