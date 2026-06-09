from __future__ import annotations

import cv2
import numpy as np


def estimate_translation_ecc(reference_gray: np.ndarray, moving_gray: np.ndarray) -> tuple[float, np.ndarray]:
    ref = np.clip(reference_gray, 0.0, 1.0).astype(np.float32)
    mov = np.clip(moving_gray, 0.0, 1.0).astype(np.float32)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        score, warp = cv2.findTransformECC(
            ref,
            mov,
            warp,
            cv2.MOTION_TRANSLATION,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-5),
        )
        return float(score), warp.astype(np.float32)
    except Exception:
        return 0.0, np.eye(2, 3, dtype=np.float32)

