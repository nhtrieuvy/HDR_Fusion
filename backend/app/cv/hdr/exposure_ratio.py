from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ExposureRatioResult:
    ratios: np.ndarray
    confidence: np.ndarray
    valid_pixel_counts: np.ndarray
    warnings: list[str]


def estimate_exposure_ratios_from_raw_overlap(
    stack: np.ndarray,
    reference_index: int,
    low_threshold: float = 0.02,
    high_threshold: float = 0.90,
) -> ExposureRatioResult:
    ref = stack[reference_index].astype(np.float32)
    ratios = np.ones(stack.shape[0], dtype=np.float32)
    confidence = np.zeros(stack.shape[0], dtype=np.float32)
    counts = np.zeros(stack.shape[0], dtype=np.int64)
    warnings: list[str] = []
    ref_mask = (ref > low_threshold) & (ref < high_threshold)
    for i, frame in enumerate(stack.astype(np.float32)):
        mask = ref_mask & (frame > low_threshold) & (frame < high_threshold)
        counts[i] = int(mask.sum())
        if counts[i] < 128:
            warnings.append(f"frame_{i}: low overlap pixels for exposure ratio")
            ratios[i] = 1.0
            confidence[i] = 0.0
            continue
        sample_ratio = frame[mask] / np.maximum(ref[mask], 1e-8)
        sample_ratio = sample_ratio[np.isfinite(sample_ratio)]
        if sample_ratio.size == 0:
            warnings.append(f"frame_{i}: invalid ratio samples")
            continue
        ratios[i] = float(np.median(np.clip(sample_ratio, 1e-4, 1e4)))
        confidence[i] = float(min(1.0, counts[i] / max(ref.size * 0.05, 1)))
    ratios[reference_index] = 1.0
    confidence[reference_index] = 1.0
    return ExposureRatioResult(ratios, confidence, counts, warnings)

