import numpy as np

from app.cv.qc.report import score_candidate, select_best_candidate


def test_qc_catches_clipped_candidate():
    clipped = np.ones((32, 32, 3), dtype=np.uint8) * 255
    good = np.ones((32, 32, 3), dtype=np.uint8) * 180
    source_mask = np.zeros((32, 32), dtype=bool)
    reports = [
        score_candidate("clipped", clipped, {}, source_mask),
        score_candidate("good", good, {}, source_mask),
    ]
    selected = select_best_candidate(reports)
    assert selected["selected_candidate"] == "good"

