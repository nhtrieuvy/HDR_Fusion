from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateConfig:
    name: str
    exposure: float
    shadow_lift: float
    saturation: float
    deglare_strength: float
    debloom_strength: float
    sharpen_amount: float
    final_p99_target: float


def candidate_configs(
    *,
    deglare_strength: float = 0.18,
    debloom_strength: float = 0.20,
    saturation_freshness: float = 1.08,
    shadow_lift: float = 0.045,
    sharpening: float = 0.20,
    final_p99_target: float = 0.89,
) -> list[CandidateConfig]:
    deglare = deglare_strength
    debloom = debloom_strength
    saturation = saturation_freshness
    shadow = shadow_lift
    sharp = sharpening
    p99 = final_p99_target
    return [
        CandidateConfig("natural", 1.05, shadow * 1.05, saturation * 1.00, deglare, debloom, sharp, p99),
        CandidateConfig("bright", 1.13, shadow * 1.20, saturation * 1.02, deglare * 0.92, debloom * 0.90, sharp * 0.92, min(0.92, p99 + 0.02)),
        CandidateConfig("conservative_hdr", 0.98, shadow * 0.92, saturation * 0.96, deglare * 1.25, debloom * 1.30, sharp * 0.80, max(0.84, p99 - 0.02)),
        CandidateConfig("window_control", 0.96, shadow * 1.00, saturation * 0.98, deglare * 1.55, debloom * 1.65, sharp * 0.78, max(0.82, p99 - 0.035)),
        CandidateConfig("artifact_safe", 0.98, shadow * 0.84, saturation * 0.92, deglare * 0.58, debloom * 0.60, sharp * 0.62, max(0.84, p99 - 0.02)),
    ]
