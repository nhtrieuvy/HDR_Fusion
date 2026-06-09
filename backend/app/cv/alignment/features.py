from __future__ import annotations

import numpy as np


def feature_translation_initialization(reference: np.ndarray, moving: np.ndarray) -> np.ndarray:
    return np.eye(2, 3, dtype=np.float32)

