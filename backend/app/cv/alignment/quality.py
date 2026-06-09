from __future__ import annotations

import numpy as np


def alignment_residual(reference: np.ndarray, moving: np.ndarray) -> float:
    ref = reference.astype(np.float32)
    mov = moving.astype(np.float32)
    return float(np.mean(np.abs(ref - mov)))

