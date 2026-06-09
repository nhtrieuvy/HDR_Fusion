from __future__ import annotations

import numpy as np


def mosaic_to_preview_gray(mosaic: np.ndarray) -> np.ndarray:
    data = np.clip(mosaic.astype(np.float32), 0.0, 1.0)
    p99 = float(np.percentile(data, 99.0))
    if p99 > 1e-6:
        data = data / p99
    return np.clip(data, 0.0, 1.0)

