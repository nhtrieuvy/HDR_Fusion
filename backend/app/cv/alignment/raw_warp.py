from __future__ import annotations

import cv2
import numpy as np


def warp_raw_mosaic_safely(
    raw_mosaic: np.ndarray,
    warp: np.ndarray,
    cfa_pattern: tuple[str, str, str, str] | None = None,
    proxy_shape: tuple[int, int] | None = None,
) -> np.ndarray:
    # Translation-only warp keeps the Bayer lattice stable when rounded to even-pixel movement.
    safe = warp.astype(np.float32).copy()
    safe[0, 2] = float(np.round(safe[0, 2] / 2.0) * 2.0)
    safe[1, 2] = float(np.round(safe[1, 2] / 2.0) * 2.0)
    h, w = raw_mosaic.shape[:2]
    return cv2.warpAffine(
        raw_mosaic.astype(np.float32),
        safe,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT101,
    ).astype(np.float32)

