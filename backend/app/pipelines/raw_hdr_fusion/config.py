from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PipelineConfig:
    input_min_frames: int = 3
    input_max_frames: int = 7
    raw_decode_no_auto_bright: bool = True
    raw_decode_gamma: tuple[float, float] = (1.0, 1.0)
    exposure_ratio_low_threshold: float = 0.02
    exposure_ratio_high_threshold: float = 0.90
    source_mask_strictness: float = 0.78
    raw_merge_low_threshold: float = 0.018
    raw_merge_high_threshold: float = 0.945
    source_compositor_strength: float = 0.90
    source_feather_sigma: float = 2.0
    window_compositor_strength: float = 1.0
    window_feather_sigma: float = 1.35
    window_detail_min_std: float = 0.018
    window_detail_min_fraction: float = 0.03
    amaze_input_percentile: float = 99.9
    amaze_input_white: float = 0.84
    amaze_input_shoulder_strength: float = 0.55
    amaze_source_ceiling_ratio: float = 0.92
    finishing_deglare_strength: float = 0.18
    finishing_debloom_strength: float = 0.20
    finishing_saturation_freshness: float = 1.08
    finishing_shadow_lift: float = 0.045
    finishing_sharpening: float = 0.20
    finishing_final_p99_target: float = 0.89
    neutral_balance_strength: float = 0.24
    neutral_balance_max_gain: float = 1.10
    highlight_chroma_strength: float = 0.20
    highlight_source_chroma_strength: float = 0.58
    shadow_chroma_strength: float = 0.14
    color_vibrance_strength: float = 0.22
    color_wood_warmth_strength: float = 0.06
    color_clarity_strength: float = 0.07
    color_source_protection: float = 0.96
    color_neutral_protection: float = 0.72
    jpeg_quality: int = 92


def config_from_snapshot(snapshot: dict[str, Any] | None) -> PipelineConfig:
    data = snapshot or {}
    input_cfg = data.get("input", {})
    raw_cfg = data.get("raw", {})
    hdr_cfg = data.get("hdr", {})
    safety_cfg = data.get("radiance_safety", {})
    finishing_cfg = data.get("finishing", {})
    color_cfg = data.get("color_grade", {})
    return PipelineConfig(
        input_min_frames=int(input_cfg.get("min_frames", 3)),
        input_max_frames=int(input_cfg.get("max_frames", 7)),
        raw_decode_no_auto_bright=bool(raw_cfg.get("no_auto_bright", True)),
        raw_decode_gamma=tuple(raw_cfg.get("gamma", [1.0, 1.0]))[:2],  # type: ignore[arg-type]
        exposure_ratio_low_threshold=float(hdr_cfg.get("exposure_ratio_low_threshold", 0.02)),
        exposure_ratio_high_threshold=float(hdr_cfg.get("exposure_ratio_high_threshold", 0.90)),
        source_mask_strictness=float(hdr_cfg.get("source_mask_strictness", 0.78)),
        raw_merge_low_threshold=float(hdr_cfg.get("raw_merge_low_threshold", 0.018)),
        raw_merge_high_threshold=float(hdr_cfg.get("raw_merge_high_threshold", 0.945)),
        source_compositor_strength=float(hdr_cfg.get("source_compositor_strength", 0.90)),
        source_feather_sigma=float(hdr_cfg.get("source_feather_sigma", 2.0)),
        window_compositor_strength=float(hdr_cfg.get("window_compositor_strength", hdr_cfg.get("source_compositor_strength", 1.0))),
        window_feather_sigma=float(hdr_cfg.get("window_feather_sigma", 1.35)),
        window_detail_min_std=float(hdr_cfg.get("window_detail_min_std", 0.018)),
        window_detail_min_fraction=float(hdr_cfg.get("window_detail_min_fraction", 0.03)),
        amaze_input_percentile=float(safety_cfg.get("amaze_input_percentile", 99.9)),
        amaze_input_white=float(safety_cfg.get("amaze_input_white", 0.84)),
        amaze_input_shoulder_strength=float(safety_cfg.get("shoulder_strength", 0.55)),
        amaze_source_ceiling_ratio=float(safety_cfg.get("source_ceiling_ratio", 0.92)),
        finishing_deglare_strength=float(finishing_cfg.get("deglare_strength", 0.18)),
        finishing_debloom_strength=float(finishing_cfg.get("debloom_strength", 0.20)),
        finishing_saturation_freshness=float(finishing_cfg.get("saturation_freshness", 1.08)),
        finishing_shadow_lift=float(finishing_cfg.get("shadow_lift", 0.045)),
        finishing_sharpening=float(finishing_cfg.get("sharpening", 0.20)),
        finishing_final_p99_target=float(finishing_cfg.get("final_p99_target", 0.89)),
        neutral_balance_strength=float(finishing_cfg.get("neutral_balance_strength", 0.24)),
        neutral_balance_max_gain=float(finishing_cfg.get("neutral_balance_max_gain", 1.10)),
        highlight_chroma_strength=float(finishing_cfg.get("highlight_chroma_strength", 0.20)),
        highlight_source_chroma_strength=float(finishing_cfg.get("highlight_source_chroma_strength", 0.58)),
        shadow_chroma_strength=float(finishing_cfg.get("shadow_chroma_strength", 0.14)),
        color_vibrance_strength=float(color_cfg.get("vibrance_strength", 0.22)),
        color_wood_warmth_strength=float(color_cfg.get("wood_warmth_strength", 0.06)),
        color_clarity_strength=float(color_cfg.get("clarity_strength", 0.07)),
        color_source_protection=float(color_cfg.get("source_protection", 0.96)),
        color_neutral_protection=float(color_cfg.get("neutral_protection", 0.72)),
        jpeg_quality=int(data.get("export", {}).get("jpeg_quality", 92)),
    )
