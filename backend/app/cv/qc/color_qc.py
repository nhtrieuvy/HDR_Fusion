from __future__ import annotations

import numpy as np


def color_cast_score(image: np.ndarray) -> float:
    rgb = image.astype(np.float32) / 255.0
    maxc = np.max(rgb, axis=-1)
    minc = np.min(rgb, axis=-1)
    sat = (maxc - minc) / np.maximum(maxc, 1e-6)
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    scores: list[float] = []
    neutral = (sat < 0.22) & (luma > 0.18) & (luma < 0.86)
    if np.count_nonzero(neutral) >= 128:
        mean = np.median(rgb[neutral], axis=0)
        scores.append(_cast_from_mean(mean))
    midtone = (sat < 0.65) & (luma > 0.14) & (luma < 0.90)
    if np.count_nonzero(midtone) >= 128:
        scores.append(_cast_from_mean(np.median(rgb[midtone], axis=0)))
    broad = (luma > 0.14) & (luma < 0.90)
    if np.count_nonzero(broad) >= 128:
        scores.append(_cast_from_mean(np.median(rgb[broad], axis=0)))
    if not scores:
        return 1.0
    return float(max(scores))


def colorfulness_score(image: np.ndarray) -> float:
    rgb = image.astype(np.float32) / 255.0
    rg = rgb[..., 0] - rgb[..., 1]
    yb = 0.5 * (rgb[..., 0] + rgb[..., 1]) - rgb[..., 2]
    std = np.sqrt(float(np.var(rg) + np.var(yb)))
    mean = np.sqrt(float(np.mean(rg) ** 2 + np.mean(yb) ** 2))
    return float(std + 0.30 * mean)


def _cast_from_mean(mean: np.ndarray) -> float:
    chroma = np.max(np.abs(mean - np.mean(mean)))
    yellow_bias = max(0.0, float((mean[0] + mean[1]) * 0.5 - mean[2]))
    return float(max(chroma, yellow_bias * 0.7))
