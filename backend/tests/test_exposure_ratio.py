import numpy as np

from app.cv.hdr.exposure_ratio import estimate_exposure_ratios_from_raw_overlap


def test_exposure_ratio_ignores_clipped_pixels():
    ref = np.full((32, 32), 0.25, dtype=np.float32)
    bright = ref * 4.0
    bright[:8, :8] = 1.0
    dark = ref * 0.25
    stack = np.stack([dark, ref, bright], axis=0)
    result = estimate_exposure_ratios_from_raw_overlap(stack, reference_index=1, low_threshold=0.02, high_threshold=0.90)
    assert abs(result.ratios[0] - 0.25) < 0.02
    assert abs(result.ratios[2] - 1.0) < 0.02  # clipped bright samples excluded, remaining unclipped are 1.0 due mask

