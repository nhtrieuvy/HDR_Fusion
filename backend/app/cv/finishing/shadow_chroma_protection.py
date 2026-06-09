from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ShadowChromaResult:
    image: np.ndarray
    amount: np.ndarray
    metrics: dict[str, float]


def protect_shadow_chroma(rgb: np.ndarray, strength: float = 0.18) -> ShadowChromaResult:
    image = rgb.astype(np.float32)
    luma = 0.2126 * image[..., 0] + 0.7152 * image[..., 1] + 0.0722 * image[..., 2]
    amount = np.clip((0.20 - luma) / 0.20, 0.0, 1.0) * strength
    neutral = luma[..., None]
    out = image * (1.0 - amount[..., None]) + neutral * amount[..., None]
    return ShadowChromaResult(out.astype(np.float32), amount.astype(np.float32), {"shadow_chroma_protection_coverage": float(np.mean(amount > 0.01))})

