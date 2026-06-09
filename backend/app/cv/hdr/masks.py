from __future__ import annotations

import numpy as np


def mask_coverage(mask: np.ndarray) -> float:
    return float(np.mean(mask.astype(bool)))

