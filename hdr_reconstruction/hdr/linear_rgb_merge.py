from __future__ import annotations

import numpy as np

from hdr_reconstruction.hdr.base import HDRResult, SceneData
from hdr_reconstruction.tonemapping.tonemap import tone_map_with_metadata
from hdr_reconstruction.utils.image_utils import hdr_statistics, sanitize_float_image
from hdr_reconstruction.utils.timer import timed


class LinearRGBMerge:
    name = "linear_rgb_merge"

    def reconstruct(self, scene_data: SceneData, config: dict) -> HDRResult:
        result = HDRResult(algorithm_name=self.name)
        with timed() as timer:
            stack = np.stack([sanitize_float_image(frame.linear_rgb) for frame in scene_data.frames], axis=0)
            times = scene_data.exposure_times.astype(np.float32).reshape(-1, 1, 1, 1)
            valid_intensity = (stack > 0.001) & (stack < 0.995)
            radiance = stack / np.maximum(times, 1e-12)
            valid_counts = np.sum(valid_intensity, axis=0).astype(np.float32)
            summed = np.sum(np.where(valid_intensity, radiance, 0.0), axis=0)
            fallback = np.mean(radiance, axis=0)
            hdr = np.where(valid_counts > 0, summed / np.maximum(valid_counts, 1.0), fallback)
            hdr = sanitize_float_image(hdr).astype(np.float32)
            result.hdr_radiance_map = hdr
            preview = tone_map_with_metadata(hdr, config)
            result.preview_png = preview.image
            result.metadata.update(hdr_statistics(hdr))
            result.metadata["tone_mapping"] = preview.metadata
        result.runtime_seconds = timer.elapsed
        return result
