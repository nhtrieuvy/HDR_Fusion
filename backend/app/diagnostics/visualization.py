from __future__ import annotations

import numpy as np


def float_to_uint8_preview(arr: np.ndarray) -> np.ndarray:
    data = arr.astype(np.float32)
    if data.ndim == 2:
        p99 = float(np.percentile(data, 99))
        if p99 > 1e-8:
            data = data / p99
        data = np.repeat(np.clip(data, 0, 1)[..., None], 3, axis=-1)
    return (np.clip(data, 0.0, 1.0) * 255.0).astype(np.uint8)

