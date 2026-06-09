from __future__ import annotations

import numpy as np


def smooth_exposure_weights(values: np.ndarray, low: float = 0.018, high: float = 0.945) -> np.ndarray:
    data = np.clip(values.astype(np.float32), 0.0, 1.0)
    mid = 0.5 * (low + high)
    weights = np.zeros_like(data, dtype=np.float32)
    rising = (data > low) & (data <= mid)
    falling = (data > mid) & (data < high)
    weights[rising] = (data[rising] - low) / max(mid - low, 1e-8)
    weights[falling] = (high - data[falling]) / max(high - mid, 1e-8)
    shoulder = np.clip((high - data) / max(1.0 - high, 1e-8), 0.0, 1.0)
    weights *= shoulder
    return np.clip(weights, 0.0, 1.0)

