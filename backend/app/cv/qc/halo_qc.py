from __future__ import annotations

import cv2
import numpy as np

from app.cv.qc.exposure_qc import luminance_uint8


def halo_score(image: np.ndarray, source_mask: np.ndarray) -> float:
    luma = luminance_uint8(image)
    ring = cv2.dilate(source_mask.astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool) & ~source_mask
    if not np.any(ring):
        return 0.0
    return float(np.mean(luma[ring] > 0.82))

