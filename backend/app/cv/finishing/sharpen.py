from __future__ import annotations

import cv2
import numpy as np


def sharpen_uint8(image: np.ndarray, amount: float = 0.22) -> np.ndarray:
    blurred = cv2.GaussianBlur(image, (0, 0), 0.8)
    return cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)

