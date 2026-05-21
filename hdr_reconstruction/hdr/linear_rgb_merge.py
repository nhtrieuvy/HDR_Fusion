from __future__ import annotations

import numpy as np

from hdr_reconstruction.hdr.base import HDRResult, SceneData
from hdr_reconstruction.hdr.merge_utils import finalize_hdr_result, finalize_weighted_average, init_accumulators
from hdr_reconstruction.utils.image_utils import sanitize_float_image
from hdr_reconstruction.utils.timer import timed


class LinearRGBMerge:
    name = "linear_rgb_merge"

    def reconstruct(self, scene_data: SceneData, config: dict) -> HDRResult:
        result = HDRResult(algorithm_name=self.name)
        merge_config = config.get("linear_merge", {})
        low = float(merge_config.get("low_threshold", 0.001))
        high = float(merge_config.get("high_threshold", 0.995))
        eps = float(merge_config.get("epsilon", 1e-8))

        with timed() as timer:
            shape = scene_data.frames[0].linear_rgb.shape
            numerator, denominator, fallback_sum = init_accumulators(shape)
            valid_min = 1.0
            valid_max = 0.0

            for frame, exposure_time in zip(scene_data.frames, scene_data.exposure_times):
                image = sanitize_float_image(frame.linear_rgb)
                radiance = image / max(float(exposure_time), 1e-12)
                valid = ((image > low) & (image < high)).astype(np.float32)
                numerator += valid * radiance
                denominator += valid
                fallback_sum += radiance
                valid_ratio = float(np.mean(valid))
                valid_min = min(valid_min, valid_ratio)
                valid_max = max(valid_max, valid_ratio)

            hdr = finalize_weighted_average(numerator, denominator, fallback_sum, len(scene_data.frames), eps)
            finalize_hdr_result(result, hdr, config)
            result.metadata.update(
                {
                    "merge_mode": "streaming_valid_pixel_average",
                    "valid_low_threshold": low,
                    "valid_high_threshold": high,
                    "valid_ratio_min": valid_min,
                    "valid_ratio_max": valid_max,
                    "zero_valid_ratio": float(np.mean(denominator <= eps)),
                }
            )
        result.runtime_seconds = timer.elapsed
        return result
