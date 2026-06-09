import numpy as np

from app.cv.hdr.merge_raw_domain import merge_raw_domain_weighted_with_debug


def test_raw_merge_rejects_saturated_source_pixels():
    dark = np.full((16, 16), 0.2, dtype=np.float32)
    mid = np.full((16, 16), 0.5, dtype=np.float32)
    bright = np.full((16, 16), 0.99, dtype=np.float32)
    stack = np.stack([dark, mid, bright])
    result = merge_raw_domain_weighted_with_debug(stack, np.array([0.5, 1.0, 2.0], dtype=np.float32), {"high_threshold": 0.94})
    assert result.metrics["clipped_rejection_percentage"] == 100.0
    assert np.max(result.weights[2]) == 0.0

