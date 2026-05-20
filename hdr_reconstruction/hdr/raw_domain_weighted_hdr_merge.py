from __future__ import annotations

import cv2
import numpy as np

from hdr_reconstruction.hdr.base import HDRResult, SceneData
from hdr_reconstruction.tonemapping.tonemap import tone_map_with_metadata
from hdr_reconstruction.utils.image_utils import hdr_statistics, sanitize_float_image
from hdr_reconstruction.utils.timer import timed


class RawDomainWeightedHDRMerge:
    name = "raw_domain_weighted_hdr_merge"

    def reconstruct(self, scene_data: SceneData, config: dict) -> HDRResult:
        result = HDRResult(algorithm_name=self.name)
        merge_config = config.get("raw_domain_weighted_merge", config.get("weighted_merge", {}))
        low = float(merge_config.get("low_threshold", 0.01))
        high = float(merge_config.get("high_threshold", 0.98))
        eps = float(merge_config.get("epsilon", 1e-8))

        with timed() as timer:
            stack = np.stack([sanitize_float_image(frame.raw_mosaic) for frame in scene_data.frames], axis=0)
            times_shape = (scene_data.exposure_times.shape[0],) + (1,) * (stack.ndim - 1)
            times = scene_data.exposure_times.astype(np.float32).reshape(times_shape)
            radiance_stack = stack / np.maximum(times, 1e-12)
            weights = _triangular_weights(stack, low, high)

            weighted_sum = np.sum(weights * radiance_stack, axis=0)
            weight_sum = np.sum(weights, axis=0)
            fallback = np.mean(radiance_stack, axis=0)
            raw_radiance = np.where(weight_sum > eps, weighted_sum / np.maximum(weight_sum, eps), fallback)
            raw_radiance = sanitize_float_image(raw_radiance).astype(np.float32)

            cfa_pattern = scene_data.frames[0].cfa_pattern or ("R", "G", "G", "B")
            wb_gains = _white_balance_gains(scene_data)
            camera_rgb_hdr = _raw_radiance_to_rgb(raw_radiance, cfa_pattern, wb_gains)
            color_matrix, color_info = _estimate_scene_color_correction(scene_data, cfa_pattern, wb_gains)
            hdr = _apply_color_matrix(camera_rgb_hdr, color_matrix)
            hdr = sanitize_float_image(hdr).astype(np.float32)

            result.hdr_radiance_map = hdr
            preview = tone_map_with_metadata(hdr, config)
            result.preview_png = preview.image
            result.metadata.update(hdr_statistics(hdr))
            result.metadata["tone_mapping"] = preview.metadata
            result.metadata.update(
                {
                    "raw_domain": True,
                    "raw_merge_domain": "black_corrected_white_normalized_mosaic",
                    "raw_demosaic": "bilinear_float_after_hdr_merge" if raw_radiance.ndim == 2 else "packed_raw_planes_to_rgb",
                    "raw_color_space": "linear_srgb_after_scene_color_correction",
                    "raw_color_correction": color_info,
                    "cfa_pattern": list(cfa_pattern),
                    "weight_min": float(np.min(weights)),
                    "weight_max": float(np.max(weights)),
                    "weight_mean": float(np.mean(weights)),
                    "zero_weight_ratio": float(np.mean(weight_sum <= eps)),
                    "raw_radiance_min": float(np.min(raw_radiance)),
                    "raw_radiance_max": float(np.max(raw_radiance)),
                    "raw_radiance_mean": float(np.mean(raw_radiance)),
                }
            )
        result.runtime_seconds = timer.elapsed
        return result


def _triangular_weights(values: np.ndarray, low: float, high: float) -> np.ndarray:
    clipped = np.clip(values, 0.0, 1.0)
    midpoint = 0.5 * (low + high)
    weights = np.zeros_like(clipped, dtype=np.float32)
    rising = (clipped >= low) & (clipped <= midpoint)
    falling = (clipped > midpoint) & (clipped <= high)
    weights[rising] = (clipped[rising] - low) / max(midpoint - low, 1e-8)
    weights[falling] = (high - clipped[falling]) / max(high - midpoint, 1e-8)
    return np.clip(weights, 0.0, 1.0)


def _white_balance_gains(scene_data: SceneData) -> dict[str, float]:
    wb = scene_data.frames[0].metadata.white_balance
    if not wb or len(wb) < 3:
        return {"R": 1.0, "G": 1.0, "B": 1.0}
    red = float(wb[0])
    green_values = [float(wb[1])] if float(wb[1]) > 0 else []
    if len(wb) > 3:
        green4 = float(wb[3])
        if green4 > 0:
            green_values.append(green4)
    green = float(np.mean(green_values)) if green_values else 1.0
    blue = float(wb[2])
    norm = max(green, 1e-8)
    return {"R": red / norm, "G": 1.0, "B": blue / norm}


def _raw_radiance_to_rgb(
    raw_radiance: np.ndarray,
    cfa_pattern: tuple[str, ...],
    wb_gains: dict[str, float],
) -> np.ndarray:
    if raw_radiance.ndim == 2:
        pattern4 = tuple(cfa_pattern[:4]) if len(cfa_pattern) >= 4 else ("R", "G", "G", "B")
        return _demosaic_bilinear_float(raw_radiance, pattern4, wb_gains)
    if raw_radiance.ndim == 3:
        return _packed_planes_to_rgb(raw_radiance, cfa_pattern, wb_gains)
    raise ValueError(f"Unsupported RAW radiance shape: {raw_radiance.shape}")


def _packed_planes_to_rgb(
    raw_radiance: np.ndarray,
    plane_colors: tuple[str, ...],
    wb_gains: dict[str, float],
) -> np.ndarray:
    channels = []
    for color in ("R", "G", "B"):
        matching = [
            raw_radiance[..., idx]
            for idx, plane_color in enumerate(plane_colors[: raw_radiance.shape[-1]])
            if plane_color.upper() == color and _is_active_plane(raw_radiance[..., idx])
        ]
        if matching:
            channel = np.mean(np.stack(matching, axis=0), axis=0)
        else:
            channel = np.zeros(raw_radiance.shape[:2], dtype=np.float32)
        channels.append(channel * float(wb_gains.get(color, 1.0)))
    return np.stack(channels, axis=-1).astype(np.float32)


def _is_active_plane(plane: np.ndarray) -> bool:
    return bool(np.percentile(plane, 99.0) > 1e-8)


def _estimate_scene_color_correction(
    scene_data: SceneData,
    cfa_pattern: tuple[str, ...],
    wb_gains: dict[str, float],
) -> tuple[np.ndarray, dict]:
    ref_idx = int(scene_data.alignment_info.get("reference_index", len(scene_data.frames) // 2))
    ref_frame = scene_data.frames[ref_idx]
    source = _raw_radiance_to_rgb(ref_frame.raw_mosaic, cfa_pattern, wb_gains)
    target = sanitize_float_image(ref_frame.linear_rgb)

    source_samples, target_samples = _sample_color_fit_pixels(source, target)
    if source_samples.shape[0] < 256:
        return np.eye(3, dtype=np.float32), {
            "status": "identity_insufficient_samples",
            "reference_file": ref_frame.metadata.filename,
            "sample_count": int(source_samples.shape[0]),
        }

    matrix, *_ = np.linalg.lstsq(source_samples, target_samples, rcond=None)
    matrix = matrix.astype(np.float32)
    return matrix, {
        "status": "least_squares_fit_to_rawpy_linear_srgb",
        "reference_file": ref_frame.metadata.filename,
        "sample_count": int(source_samples.shape[0]),
        "matrix": matrix.tolist(),
    }


def _sample_color_fit_pixels(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    source = sanitize_float_image(source)
    target = sanitize_float_image(target)
    luminance = 0.2126 * target[..., 0] + 0.7152 * target[..., 1] + 0.0722 * target[..., 2]
    mask = (
        np.isfinite(source).all(axis=-1)
        & np.isfinite(target).all(axis=-1)
        & (luminance > 0.02)
        & (luminance < 0.90)
        & (np.max(source, axis=-1) > 1e-6)
        & (np.max(source, axis=-1) < 0.98)
    )
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return np.empty((0, 3), dtype=np.float32), np.empty((0, 3), dtype=np.float32)

    max_samples = 200000
    stride = max(1, ys.size // max_samples)
    ys = ys[::stride]
    xs = xs[::stride]
    return source[ys, xs].reshape(-1, 3), target[ys, xs].reshape(-1, 3)


def _apply_color_matrix(image: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    converted = image.reshape(-1, 3) @ matrix
    converted = converted.reshape(image.shape)
    return np.maximum(converted, 0.0).astype(np.float32)


def _demosaic_bilinear_float(
    raw_radiance: np.ndarray,
    cfa_pattern: tuple[str, str, str, str],
    wb_gains: dict[str, float],
) -> np.ndarray:
    h, w = raw_radiance.shape
    channels = []
    for color in ("R", "G", "B"):
        mask = _cfa_mask(h, w, cfa_pattern, color)
        samples = raw_radiance * mask
        interpolated = _normalized_blur(samples, mask)
        channels.append(interpolated * float(wb_gains.get(color, 1.0)))
    return np.stack(channels, axis=-1).astype(np.float32)


def _cfa_mask(height: int, width: int, pattern: tuple[str, str, str, str], color: str) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.float32)
    positions = ((0, 0), (0, 1), (1, 0), (1, 1))
    for (row_offset, col_offset), cfa_color in zip(positions, pattern):
        if cfa_color.upper() == color:
            mask[row_offset::2, col_offset::2] = 1.0
    return mask


def _normalized_blur(values: np.ndarray, mask: np.ndarray) -> np.ndarray:
    kernel = np.array(
        [
            [1.0, 2.0, 1.0],
            [2.0, 4.0, 2.0],
            [1.0, 2.0, 1.0],
        ],
        dtype=np.float32,
    )
    numerator = cv2.filter2D(values, -1, kernel, borderType=cv2.BORDER_REFLECT)
    denominator = cv2.filter2D(mask, -1, kernel, borderType=cv2.BORDER_REFLECT)
    return numerator / np.maximum(denominator, 1e-8)
