from __future__ import annotations

import numpy as np

from app.cv.qc.exposure_qc import luminance_uint8


def clipping_metrics(image: np.ndarray) -> dict[str, float]:
    luma = luminance_uint8(image)
    return {
        "final_highlight_clipping": float(np.mean(luma >= 0.995) * 100.0),
        "technical_clipping_after_processing": float(np.mean(np.max(image, axis=-1) >= 254) * 100.0),
        "final_p95_luminance": float(np.percentile(luma, 95)),
        "final_p99_luminance": float(np.percentile(luma, 99)),
    }

