from __future__ import annotations

import numpy as np

from hdr_reconstruction.hdr.base import HDRResult, SceneData
from hdr_reconstruction.tonemapping.tonemap import tone_map_with_metadata
from hdr_reconstruction.utils.image_utils import hdr_statistics, sanitize_float_image
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
            stack = np.stack([sanitize_float_image(frame.linear_rgb) for frame in scene_data.frames], axis=0)
            times = scene_data.exposure_times.astype(np.float32).reshape(-1, 1, 1, 1)
            radiance = stack / np.maximum(times, 1e-12)

            luminance = (
                0.2126 * stack[..., 0]
                + 0.7152 * stack[..., 1]
                + 0.0722 * stack[..., 2]
            ).astype(np.float32)
            exposure_quality = _triangular_weights(luminance, low, high).astype(np.float32)

            iso_values = np.array(
                [
                    float(frame.metadata.iso)
                    if frame.metadata.iso is not None and float(frame.metadata.iso) > 0
                    else iso_reference
                    for frame in scene_data.frames
                ],
                dtype=np.float32,
            ).reshape(-1, 1, 1)
            read_noise = read_noise_base * np.power(
                np.maximum(iso_values, 1.0) / max(iso_reference, 1.0),
                iso_exponent,
            )
            signal_variance = shot_noise_factor * np.maximum(luminance, signal_floor)
            image_noise_variance = signal_variance + read_noise**2
            radiance_noise_variance = image_noise_variance / np.maximum(times[..., 0], 1e-12) ** 2
            noise_weight = 1.0 / np.maximum(radiance_noise_variance, eps)
            noise_weight = np.minimum(noise_weight, max_weight).astype(np.float32)

            weights = (exposure_quality * noise_weight).astype(np.float32)[..., None]
            weighted_sum = np.sum(weights * radiance, axis=0)
            weight_sum = np.sum(weights, axis=0)

            fallback = np.mean(radiance, axis=0)
            hdr = np.where(weight_sum > eps, weighted_sum / np.maximum(weight_sum, eps), fallback)
            hdr = sanitize_float_image(hdr).astype(np.float32)

            result.hdr_radiance_map = hdr
            preview = tone_map_with_metadata(hdr, config)
            result.preview_png = preview.image
            result.metadata.update(hdr_statistics(hdr))
            result.metadata["tone_mapping"] = preview.metadata
            result.metadata.update(
                {
                    "weight_model": "exposure_quality_inverse_radiance_noise_variance",
                    "read_noise_base": read_noise_base,
                    "iso_reference": iso_reference,
                    "read_noise_iso_exponent": iso_exponent,
                    "shot_noise_factor": shot_noise_factor,
                    "signal_floor": signal_floor,
                    "weight_min": float(np.min(weights)),
                    "weight_max": float(np.max(weights)),
                    "weight_mean": float(np.mean(weights)),
                    "noise_weight_min": float(np.min(noise_weight)),
                    "noise_weight_max": float(np.max(noise_weight)),
                    "noise_weight_mean": float(np.mean(noise_weight)),
                    "zero_weight_ratio": float(np.mean(weight_sum <= eps)),
                }
            )
        result.runtime_seconds = timer.elapsed
        return result


def _triangular_weights(luminance: np.ndarray, low: float, high: float) -> np.ndarray:
    lum = np.clip(luminance, 0.0, 1.0)
    midpoint = 0.5 * (low + high)
    weights = np.zeros_like(lum, dtype=np.float32)
    rising = (lum >= low) & (lum <= midpoint)
    falling = (lum > midpoint) & (lum <= high)
    weights[rising] = (lum[rising] - low) / max(midpoint - low, 1e-8)
    weights[falling] = (high - lum[falling]) / max(high - midpoint, 1e-8)
    return np.clip(weights, 0.0, 1.0)
