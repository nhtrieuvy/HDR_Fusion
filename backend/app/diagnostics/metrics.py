from __future__ import annotations

import numpy as np


def array_stats(prefix: str, arr: np.ndarray) -> dict[str, float]:
    data = arr.astype(np.float32)
    return {
        f"{prefix}_min": float(np.min(data)),
        f"{prefix}_max": float(np.max(data)),
        f"{prefix}_median": float(np.median(data)),
        f"{prefix}_p95": float(np.percentile(data, 95)),
        f"{prefix}_p99": float(np.percentile(data, 99)),
    }

