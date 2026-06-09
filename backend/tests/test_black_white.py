import numpy as np

from app.cv.raw.black_white import normalize_raw_mosaic


def test_black_white_normalization_preserves_clipping_stats():
    raw = np.array([[64, 128], [1023, 2048]], dtype=np.float32)
    result = normalize_raw_mosaic(raw, black_level=[64, 64, 64, 64], white_level=1023)
    assert result.mosaic[0, 0] == 0.0
    assert result.metrics["raw_clip_percentage"] > 0.0
    assert result.metrics["black_level_used"] == 64.0

