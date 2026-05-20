from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def sanitize_float_image(image: np.ndarray) -> np.ndarray:
    clean = np.asarray(image, dtype=np.float32)
    clean = np.nan_to_num(clean, nan=0.0, posinf=0.0, neginf=0.0)
    return np.maximum(clean, 0.0)


def rgb_to_bgr(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def to_gray_uint8(rgb: np.ndarray) -> np.ndarray:
    if rgb.dtype != np.uint8:
        data = np.clip(rgb, 0.0, 1.0)
        rgb_u8 = (data * 255.0 + 0.5).astype(np.uint8)
    else:
        rgb_u8 = rgb
    return cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2GRAY)


def resize_to_match(image: np.ndarray, shape_hw: tuple[int, int]) -> np.ndarray:
    h, w = shape_hw
    if image.shape[:2] == (h, w):
        return image
    interpolation = cv2.INTER_AREA if image.shape[0] > h or image.shape[1] > w else cv2.INTER_LINEAR
    return cv2.resize(image, (w, h), interpolation=interpolation)


def hdr_statistics(hdr: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(hdr, dtype=np.float32)
    has_nan = bool(np.isnan(finite).any())
    has_inf = bool(np.isinf(finite).any())
    finite = sanitize_float_image(finite)
    positive = finite[finite > 0]
    if positive.size:
        low = float(np.percentile(positive, 0.1))
        high = float(np.percentile(positive, 99.9))
        dynamic_range = float(high / max(low, 1e-12))
    else:
        dynamic_range = 0.0
    max_value = float(np.max(finite)) if finite.size else 0.0
    clipping_ratio = float(np.mean(finite >= max_value)) if max_value > 0 else 0.0
    return {
        "hdr_min": float(np.min(finite)) if finite.size else 0.0,
        "hdr_max": max_value,
        "hdr_mean": float(np.mean(finite)) if finite.size else 0.0,
        "hdr_dynamic_range_estimate": dynamic_range,
        "has_nan": has_nan,
        "has_inf": has_inf,
        "nan_count": int(np.isnan(hdr).sum()),
        "inf_count": int(np.isinf(hdr).sum()),
        "clipping_ratio": clipping_ratio,
    }

