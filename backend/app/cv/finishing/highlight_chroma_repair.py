from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class ChromaRepairResult:
    image: np.ndarray
    mask: np.ndarray
    metrics: dict[str, float]


def repair_highlight_chroma(
    rgb: np.ndarray,
    strength: float = 0.25,
    source_mask: np.ndarray | None = None,
    source_strength: float = 0.62,
) -> ChromaRepairResult:
    image = rgb.astype(np.float32)
    luma = 0.2126 * image[..., 0] + 0.7152 * image[..., 1] + 0.0722 * image[..., 2]
    maxc = np.max(image, axis=-1)
    minc = np.min(image, axis=-1)
    sat = (maxc - minc) / np.maximum(maxc, 1e-6)
    mask = (luma > np.percentile(luma, 98.8)) & (sat > 0.12)
    amount = np.where(mask, strength, 0.0).astype(np.float32)
    if source_mask is not None:
        source = np.asarray(source_mask).astype(bool)
        halo = cv2.GaussianBlur(source.astype(np.float32), (0, 0), 9.0)
        source_chroma = (halo > 0.004) & (sat > 0.045) & (luma > np.percentile(luma, 72))
        amount = np.maximum(amount, source_chroma.astype(np.float32) * np.clip(halo * source_strength, 0.18, source_strength))
        mask |= source_chroma
    neutral = luma[..., None]
    out = image * (1.0 - amount[..., None]) + neutral * amount[..., None]
    metrics = {
        "highlight_chroma_repair_coverage": float(np.mean(mask)),
        "highlight_chroma_repair_strength": strength,
        "highlight_source_chroma_repair_strength": source_strength,
    }
    return ChromaRepairResult(out.astype(np.float32), mask, metrics)
