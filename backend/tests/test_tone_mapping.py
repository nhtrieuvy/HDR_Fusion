import numpy as np

from app.cv.finishing.tone_mapping import tone_map_interior


def test_tone_mapping_limits_final_clip_regions():
    rgb = np.ones((64, 64, 3), dtype=np.float32) * 0.35
    rgb[10:20, 10:20] = 20.0
    mask = np.zeros((64, 64), dtype=bool)
    mask[10:20, 10:20] = True
    result = tone_map_interior(rgb, source_mask=mask, final_p99_target=0.88)
    assert result.metrics["highlight_clip_percentage"] < 5.0

