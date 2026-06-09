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


class NoiseAwareWeightedLinearHDRMerge:
    name = "noise_aware_weighted_linear_hdr_merge"

    def reconstruct(self, scene_data: SceneData, config: dict) -> HDRResult:
        result = HDRResult(algorithm_name=self.name)
        merge_config = config.get("noise_aware_weighted_merge", {})
        low = float(merge_config.get("low_threshold", 0.01))
        high = float(merge_config.get("high_threshold", 0.98))
        eps = float(merge_config.get("epsilon", 1e-8))
        read_noise_base = float(merge_config.get("read_noise_base", 0.003))
        iso_reference = float(merge_config.get("iso_reference", 100.0))
        iso_exponent = float(merge_config.get("read_noise_iso_exponent", 0.5))
        shot_noise_factor = float(merge_config.get("shot_noise_factor", 1.0))
        signal_floor = float(merge_config.get("signal_floor", 1e-4))
        max_weight = float(merge_config.get("max_weight", 1e6))

        with timed() as timer:
            shape = scene_data.frames[0].linear_rgb.shape
            numerator, denominator, fallback_sum = init_accumulators(shape)
            weight_min = np.inf
            weight_max = 0.0
            weight_sum_total = 0.0
            noise_weight_min = np.inf
            noise_weight_max = 0.0
            noise_weight_sum_total = 0.0
            weight_count = 0

            for frame, exposure_time in zip(scene_data.frames, scene_data.exposure_times):
                image = sanitize_float_image(frame.linear_rgb)
                t = max(float(exposure_time), 1e-12)
                radiance = image / t
                lum = luminance(image)
                exposure_quality = triangular_weights(lum, low, high).astype(np.float32)
                iso = (
                    float(frame.metadata.iso)
                    if frame.metadata.iso is not None and float(frame.metadata.iso) > 0
                    else iso_reference
                )
                read_noise = read_noise_base * (max(iso, 1.0) / max(iso_reference, 1.0)) ** iso_exponent
                signal_variance = shot_noise_factor * np.maximum(lum, signal_floor)
                image_noise_variance = signal_variance + read_noise**2
                radiance_noise_variance = image_noise_variance / (t * t)
                noise_weight = np.minimum(1.0 / np.maximum(radiance_noise_variance, eps), max_weight).astype(np.float32)
                weights = (exposure_quality * noise_weight).astype(np.float32)[..., None]

                numerator += weights * radiance
                denominator += weights
                fallback_sum += radiance
                weight_min = min(weight_min, float(np.min(weights)))
                weight_max = max(weight_max, float(np.max(weights)))
                weight_sum_total += float(np.sum(weights))
                noise_weight_min = min(noise_weight_min, float(np.min(noise_weight)))
                noise_weight_max = max(noise_weight_max, float(np.max(noise_weight)))
                noise_weight_sum_total += float(np.sum(noise_weight))
                weight_count += int(noise_weight.size)

            hdr = finalize_weighted_average(numerator, denominator, fallback_sum, len(scene_data.frames), eps)
            finalize_hdr_result(result, hdr, config)
            result.metadata.update(
                {
                    "merge_mode": "streaming_noise_aware_luminance_weighted_average",
                    "weight_model": "exposure_quality_inverse_radiance_noise_variance",
                    "read_noise_base": read_noise_base,
                    "iso_reference": iso_reference,
                    "read_noise_iso_exponent": iso_exponent,
                    "shot_noise_factor": shot_noise_factor,
                    "signal_floor": signal_floor,
                    "weight_min": 0.0 if not np.isfinite(weight_min) else weight_min,
                    "weight_max": weight_max,
                    "weight_mean": weight_sum_total / max(weight_count, 1),
                    "noise_weight_min": 0.0 if not np.isfinite(noise_weight_min) else noise_weight_min,
                    "noise_weight_max": noise_weight_max,
                    "noise_weight_mean": noise_weight_sum_total / max(weight_count, 1),
                    "zero_weight_ratio": float(np.mean(denominator <= eps)),
                }
            )
        result.runtime_seconds = timer.elapsed
        return result
