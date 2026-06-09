import numpy as np

from app.cv.finishing.interior_color_grade import apply_interior_color_grade


def test_interior_color_grade_increases_material_color_while_protecting_neutral_and_source():
    rgb = np.zeros((32, 32, 3), dtype=np.float32) + 0.42
    rgb[:, :12, :] = 0.45
    rgb[12:26, 14:30, :] = np.array([0.46, 0.30, 0.16], dtype=np.float32)
    rgb[2:8, 24:30, :] = 1.8

    neutral = np.zeros((32, 32), dtype=bool)
    neutral[:, :12] = True
    source = np.zeros((32, 32), dtype=bool)
    source[2:8, 24:30] = True

    result = apply_interior_color_grade(
        rgb,
        source_mask=source,
        neutral_mask=neutral,
        vibrance_strength=0.24,
        wood_warmth_strength=0.08,
        clarity_strength=0.0,
    )

    assert result.metrics["colorfulness_after"] > result.metrics["colorfulness_before"]
    assert result.wood_mask[18, 20]
    assert np.allclose(result.image[16, 4], rgb[16, 4], atol=0.06)
    assert result.source_protection[4, 26] > 0.5
