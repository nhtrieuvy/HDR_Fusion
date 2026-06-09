from app.pipelines.raw_hdr_fusion.config import config_from_snapshot


def test_config_from_snapshot_reads_finishing_source_and_color_grade():
    config = config_from_snapshot(
        {
            "hdr": {
                "source_compositor_strength": 0.77,
                "source_feather_sigma": 3.1,
                "window_compositor_strength": 1.21,
                "window_feather_sigma": 1.05,
                "window_detail_min_std": 0.012,
                "window_detail_min_fraction": 0.04,
            },
            "finishing": {
                "deglare_strength": 0.31,
                "debloom_strength": 0.37,
                "saturation_freshness": 1.16,
                "final_p99_target": 0.83,
                "neutral_balance_strength": 0.19,
                "neutral_balance_max_gain": 1.05,
                "highlight_chroma_strength": 0.23,
                "highlight_source_chroma_strength": 0.71,
                "shadow_chroma_strength": 0.11,
            },
            "color_grade": {
                "vibrance_strength": 0.26,
                "wood_warmth_strength": 0.08,
                "clarity_strength": 0.04,
                "source_protection": 0.97,
                "neutral_protection": 0.75,
            },
        }
    )

    assert config.source_compositor_strength == 0.77
    assert config.source_feather_sigma == 3.1
    assert config.window_compositor_strength == 1.21
    assert config.window_detail_min_std == 0.012
    assert config.finishing_saturation_freshness == 1.16
    assert config.finishing_final_p99_target == 0.83
    assert config.neutral_balance_max_gain == 1.05
    assert config.highlight_source_chroma_strength == 0.71
    assert config.color_vibrance_strength == 0.26
    assert config.color_wood_warmth_strength == 0.08
    assert config.color_source_protection == 0.97
