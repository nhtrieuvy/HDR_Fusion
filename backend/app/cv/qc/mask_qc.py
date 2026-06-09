from __future__ import annotations

import numpy as np


def mask_leak_score(source_mask: np.ndarray, false_positive_mask: np.ndarray) -> float:
    return float(np.mean(source_mask & false_positive_mask))

