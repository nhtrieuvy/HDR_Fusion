from __future__ import annotations

import numpy as np

from hdr_reconstruction.hdr.base import HDRResult, SceneData
from hdr_reconstruction.hdr.merge_utils import (
    finalize_hdr_result,
    finalize_weighted_average,
    init_accumulators,
    luminance,
    triangular_weights,
)
from hdr_reconstruction.utils.image_utils import sanitize_float_image
from hdr_reconstruction.utils.timer import timed


class WeightedLinearRGBMerge:
    name = "weighted_linear_rgb_merge"

    def reconstruct(self, scene_data: SceneData, config: dict) -> HDRResult:
        result = HDRResult(algorithm_name=self.name)
        merge_config = config.get("weighted_merge", {})
        low = float(merge_config.get("low_threshold", 0.01))
        high = float(merge_config.get("high_threshold", 0.98))
        eps = float(merge_config.get("epsilon", 1e-8))

        with timed() as timer:
            shape = scene_data.frames[0].linear_rgb.shape
            numerator, denominator, fallback_sum = init_accumulators(shape)
            weight_min = np.inf
            weight_max = 0.0
            weight_sum_total = 0.0
            weight_count = 0

            for frame, exposure_time in zip(scene_data.frames, scene_data.exposure_times):
                image = sanitize_float_image(frame.linear_rgb)
                radiance = image / max(float(exposure_time), 1e-12)
                weights = triangular_weights(luminance(image), low, high).astype(np.float32)[..., None]
                numerator += weights * radiance
                denominator += weights
                fallback_sum += radiance
                weight_min = min(weight_min, float(np.min(weights)))
                weight_max = max(weight_max, float(np.max(weights)))
                weight_sum_total += float(np.sum(weights))
                weight_count += int(weights.size)

            hdr = finalize_weighted_average(numerator, denominator, fallback_sum, len(scene_data.frames), eps)
            finalize_hdr_result(result, hdr, config)
            result.metadata.update(
                {
                    "merge_mode": "streaming_luminance_weighted_average",
                    "weight_min": 0.0 if not np.isfinite(weight_min) else weight_min,
                    "weight_max": weight_max,
                    "weight_mean": weight_sum_total / max(weight_count, 1),
                    "zero_weight_ratio": float(np.mean(denominator <= eps)),
                }
            )
        result.runtime_seconds = timer.elapsed
        return result
