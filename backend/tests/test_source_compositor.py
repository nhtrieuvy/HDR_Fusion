import numpy as np

from app.cv.hdr.typed_source_masks import analyze_typed_source_masks
from app.cv.hdr.valid_source_compositor import composite_valid_sources


def test_source_compositor_uses_valid_dark_source_detail():
    stack = np.zeros((3, 32, 32), dtype=np.float32) + 0.25
    stack[0, 10:14, 10:14] = 0.45
    stack[1, 10:14, 10:14] = 0.94
    stack[2, 10:14, 10:14] = 0.99
    masks = analyze_typed_source_masks(stack, [0, 1, 2], 1, {"source_mask_strictness": 0.78})
    radiance_stack = stack / np.array([0.5, 1.0, 2.0], dtype=np.float32)[:, None, None]
    base = np.full((32, 32), 0.94, dtype=np.float32)
    result = composite_valid_sources(base, radiance_stack, masks)
    assert result.metrics["valid_source_detail_found"] is True
    assert result.radiance[12, 12] < base[12, 12]

