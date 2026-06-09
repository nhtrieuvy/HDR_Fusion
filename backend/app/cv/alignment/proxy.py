from __future__ import annotations

import numpy as np


def rgb_proxy_to_gray(rgb: np.ndarray) -> np.ndarray:
    if rgb.ndim == 2:
        gray = rgb.astype(np.float32)
    else:
        gray = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    p99 = float(np.percentile(gray, 99.0))
    if p99 > 1e-6:
        gray = gray / p99
    return np.clip(gray, 0.0, 1.0).astype(np.float32)

