from __future__ import annotations

from app.cv.audit.blur import blur_score


def sharpness_score(image) -> float:
    return blur_score(image / 255.0)

