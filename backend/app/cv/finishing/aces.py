from __future__ import annotations

import numpy as np


def aces_filmic(x: np.ndarray) -> np.ndarray:
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0)

