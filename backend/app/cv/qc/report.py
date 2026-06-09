from __future__ import annotations

from typing import Any

import numpy as np

from app.cv.qc.clipping_qc import clipping_metrics
from app.cv.qc.color_qc import color_cast_score, colorfulness_score
from app.cv.qc.halo_qc import halo_score
from app.cv.qc.sharpness_qc import sharpness_score


def score_candidate(candidate_name: str, image: np.ndarray, metrics: dict[str, Any], source_mask: np.ndarray) -> dict[str, Any]:
    clip = clipping_metrics(image)
    halo = halo_score(image, source_mask.astype(bool))
    color = color_cast_score(image)
    colorfulness = colorfulness_score(image)
    sharp = sharpness_score(image)
    unrecoverable = float(metrics.get("unrecoverable_source_coverage", 0.0))
    colorfulness_reward = np.clip((colorfulness - 0.035) / 0.07, 0.0, 1.0) * 0.06
    dull_penalty = 0.08 * max(0.0, min(1.0, (0.035 - colorfulness) / 0.035))
    score = (
        1.0
        - 0.45 * min(1.0, clip["technical_clipping_after_processing"] / 4.0)
        - 0.25 * min(1.0, halo)
        - 0.15 * min(1.0, color / 0.08)
        - 0.15 * min(1.0, unrecoverable / 0.02)
        - dull_penalty
        + float(colorfulness_reward)
    )
    return {
        "candidate_name": candidate_name,
        "score": float(score),
        "metrics": {
            **clip,
            "halo_score": float(halo),
            "color_cast": float(color),
            "colorfulness": float(colorfulness),
            "blur_sharpness": float(sharp),
            "unrecoverable_source_clipping": unrecoverable,
            "window_exterior_detail_confidence": float(metrics.get("window_exterior_detail_confidence", metrics.get("valid_dark_source_detail_coverage", 0.0))),
            "overall_naturalness_score": float(score),
        },
        "warnings": _candidate_warnings(clip, halo, color, unrecoverable, colorfulness),
    }


def select_best_candidate(candidate_reports: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidate_reports:
        return {"status": "manual_review", "selected_candidate": "none", "warnings": ["no_candidates"], "metrics": {}}
    best = max(candidate_reports, key=lambda item: float(item.get("score", 0.0)))
    status = "pass" if float(best.get("score", 0.0)) >= 0.65 and not best.get("warnings") else "manual_review"
    if any("technical_clipping" in w for w in best.get("warnings", [])):
        status = "qc_failed"
    return {
        "status": status,
        "selected_candidate": best["candidate_name"],
        "recommended_action": _recommended_action(status, best.get("warnings", [])),
        "warnings": best.get("warnings", []),
        "metrics": best.get("metrics", {}),
        "candidates": candidate_reports,
    }


def build_rule_based_qc_report(metrics: dict[str, Any]) -> dict[str, Any]:
    warnings = []
    if float(metrics.get("amaze_input_technical_clip_percentage", 0.0)) > 0.5:
        warnings.append("technical_clipping_before_amaze_detected")
    if float(metrics.get("unrecoverable_source_coverage", 0.0)) > 0.001:
        warnings.append("true_capture_clipping_in_darkest_raw")
    if float(metrics.get("window_core_coverage", 0.0)) > 0.0 and float(metrics.get("window_exterior_detail_confidence", 0.0)) < 0.03:
        warnings.append("window_exterior_detail_not_recoverable_from_darkest_raw")
    return {"warnings": warnings, "metrics": metrics}


def _candidate_warnings(clip: dict[str, float], halo: float, color: float, unrecoverable: float, colorfulness: float) -> list[str]:
    warnings: list[str] = []
    if clip["technical_clipping_after_processing"] > 1.0:
        warnings.append("technical_clipping_after_processing_high")
    if halo > 0.08:
        warnings.append("source_halo_score_high")
    if color > 0.08:
        warnings.append("color_cast_high")
    if colorfulness < 0.028:
        warnings.append("colorfulness_low")
    if unrecoverable > 0.001:
        warnings.append("true_capture_source_clipping_unrecoverable")
    return warnings


def _recommended_action(status: str, warnings: list[str]) -> str:
    if status == "pass":
        return "approve_candidate"
    if any("technical_clipping" in item for item in warnings):
        return "retry_with_window_control_or_conservative_hdr"
    if any("halo" in item for item in warnings):
        return "reduce_deglare_or_debloom_strength"
    if any("unrecoverable" in item for item in warnings):
        return "manual_review_true_capture_clipping"
    return "manual_review"
