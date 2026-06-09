from __future__ import annotations


def ghosting_score_from_alignment(alignment_confidence: float) -> float:
    return float(max(0.0, 1.0 - alignment_confidence))

