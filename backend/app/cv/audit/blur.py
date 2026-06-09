from __future__ import annotations

import cv2
import numpy as np


def blur_score(gray_or_rgb: np.ndarray) -> float:
    image = gray_or_rgb
    if image.ndim == 3:
        image = cv2.cvtColor((np.clip(image, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    else:
        image = (np.clip(image, 0, 1) * 255).astype(np.uint8)
    return float(cv2.Laplacian(image, cv2.CV_64F).var())

