from app.pipelines.raw_hdr_fusion.config import config_from_snapshot
from app.core.config import Settings


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


def test_settings_reads_demosaic_backend_env(monkeypatch):
    monkeypatch.setenv("DEMOSAIC_BACKEND", "external_amaze_service")
    monkeypatch.setenv("AMAZE_SERVICE_URL", "http://127.0.0.1:8077")
    monkeypatch.setenv("AMAZE_TIMEOUT_SECONDS", "99")
    monkeypatch.setenv("AMAZE_ALLOW_FALLBACK", "false")

    settings = Settings.from_env()

    assert settings.demosaic_backend == "external_amaze_service"
    assert settings.amaze_service_url == "http://127.0.0.1:8077"
    assert settings.amaze_timeout_seconds == 99
    assert settings.amaze_allow_fallback is False
