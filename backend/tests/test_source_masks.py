import numpy as np

from app.cv.hdr.typed_source_masks import analyze_typed_source_masks


def test_typed_source_masks_reject_large_bright_wall():
    stack = np.zeros((3, 80, 100), dtype=np.float32) + 0.25
    stack[:, :, :60] = 0.90  # broad bright wall
    stack[:, 20:26, 75:81] = np.array([0.5, 0.88, 0.98], dtype=np.float32)[:, None, None]  # compact light/source
    masks = analyze_typed_source_masks(stack, [0, 1, 2], 1, {"source_mask_strictness": 0.78})
    assert masks.metrics["countertop_or_wall_false_positive_coverage"] > 0.1
    assert masks.metrics["source_core_coverage"] < 0.05


def test_typed_source_masks_accept_multichannel_raw_stack():
    stack = np.zeros((3, 80, 100, 4), dtype=np.float32) + 0.25
    stack[:, 20:28, 70:78, :] = np.array([0.45, 0.86, 0.99], dtype=np.float32)[:, None, None, None]
    masks = analyze_typed_source_masks(stack, [0, 1, 2], 1, {"source_mask_strictness": 0.78})
    assert masks.source_core.shape == (80, 100)
    assert masks.source_and_bloom.shape == (80, 100)


def test_typed_source_masks_mark_window_recoverable_when_dark_raw_has_detail():
    stack = np.zeros((3, 80, 100), dtype=np.float32) + 0.25
    gradient = np.linspace(0.18, 0.52, 30, dtype=np.float32)[None, :]
    stack[0, 20:40, 50:80] = gradient
    stack[1, 20:40, 50:80] = 0.90
    stack[2, 20:40, 50:80] = 0.99

    masks = analyze_typed_source_masks(
        stack,
        [0, 1, 2],
        1,
        {"source_mask_strictness": 0.78, "window_detail_min_std": 0.01, "window_detail_min_fraction": 0.02},
    )

    assert masks.window_core[25, 60]
    assert masks.window_recoverable_detail[25, 60]
    assert masks.metrics["window_exterior_detail_confidence"] > 0.5
