import numpy as np

from app.cv.hdr.radiance_safety import prepare_amaze_input_with_safety


def test_radiance_safety_reports_technical_clipping():
    radiance = np.ones((32, 32), dtype=np.float32) * 0.5
    radiance[4:8, 4:8] = 50.0
    result = prepare_amaze_input_with_safety(radiance, input_percentile=99.0, target_white=0.8)
    assert result.metrics["amaze_input_preclip_percentage"] > 0.0
    assert result.amaze_input.max() <= 0.8 + 1e-5

