from __future__ import annotations

import numpy as np


def luminance_uint8(image: np.ndarray) -> np.ndarray:
    rgb = image.astype(np.float32) / 255.0
    linear = np.power(np.clip(rgb, 0, 1), 2.2)
    return 0.2126 * linear[..., 0] + 0.7152 * linear[..., 1] + 0.0722 * linear[..., 2]

