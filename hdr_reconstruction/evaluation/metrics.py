from __future__ import annotations

import numpy as np

from hdr_reconstruction.utils.image_utils import hdr_statistics


def compute_hdr_metrics(hdr: np.ndarray) -> dict:
    return hdr_statistics(hdr)

