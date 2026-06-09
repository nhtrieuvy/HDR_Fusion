import numpy as np

from app.cv.demosaic.amaze_adapter import demosaic_amaze_or_fallback
from app.cv.hdr.merge_raw_domain import merge_raw_domain_weighted_with_debug
from app.cv.hdr.radiance_safety import prepare_amaze_input_with_safety
from app.cv.hdr.typed_source_masks import analyze_typed_source_masks


def test_multichannel_raw_merge_safety_and_rgb_conversion():
    base = np.zeros((40, 48, 4), dtype=np.float32) + np.array([0.24, 0.26, 0.25, 0.22], dtype=np.float32)
    base[10:16, 30:36, :] = 0.92
    stack = np.stack([np.clip(base * scale, 0.0, 1.0) for scale in [0.35, 1.0, 2.5]], axis=0)

    masks = analyze_typed_source_masks(stack, [0, 1, 2], 1, {"source_mask_strictness": 0.78})
    merge = merge_raw_domain_weighted_with_debug(stack, np.array([0.35, 1.0, 2.5], dtype=np.float32))
    safety = prepare_amaze_input_with_safety(merge.radiance, masks)
    demosaic = demosaic_amaze_or_fallback(safety.amaze_input, cfa_pattern=("R", "G", "G", "B"))

    assert merge.radiance.shape == (40, 48, 4)
    assert merge.weights.shape == (3, 40, 48)
    assert safety.technical_clip_mask.shape == (40, 48)
    assert demosaic.rgb.shape == (40, 48, 3)
    assert demosaic.metrics["demosaic_method"] == "multichannel_raw_to_linear_rgb"


def test_multichannel_linear_dng_uses_rgbg_labels_and_ignores_padding_channel():
    raw = np.zeros((12, 14, 4), dtype=np.float32)
    raw[..., 0] = 0.20
    raw[..., 1] = 0.30
    raw[..., 2] = 0.10
    raw[..., 3] = 0.0

    demosaic = demosaic_amaze_or_fallback(
        raw,
        raw_channel_labels=("R", "G", "B", "G"),
        camera_wb=[1.3, 1.0, 2.0, 0.0],
        color_desc="RGBG",
    )

    assert demosaic.rgb.shape == (12, 14, 3)
    assert demosaic.metrics["camera_white_balance_applied"] is True
    assert demosaic.metrics["ignored_raw_channels"][0]["index"] == 3
    assert float(np.median(demosaic.rgb[..., 2])) > 0.19
