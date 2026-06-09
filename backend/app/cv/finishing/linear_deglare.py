from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class DeglareResult:
    image: np.ndarray
    amount: np.ndarray
    metrics: dict[str, float]


def apply_linear_deglare(rgb: np.ndarray, source_mask: np.ndarray, strength: float = 0.20) -> DeglareResult:
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    halo = cv2.GaussianBlur(source_mask.astype(np.float32), (0, 0), 7.0)
    amount = np.clip(halo * strength * np.clip(luma - 0.55, 0.0, 1.0), 0.0, 0.45)
    out = rgb * (1.0 - amount[..., None])
    metrics = {"linear_deglare_coverage": float(np.mean(amount > 0.01)), "linear_deglare_mean_amount": float(np.mean(amount))}
    return DeglareResult(out.astype(np.float32), amount.astype(np.float32), metrics)

