from __future__ import annotations

import cv2
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


class RawDomainWeightedHDRMerge:
    name = "raw_domain_weighted_hdr_merge"

    def reconstruct(self, scene_data: SceneData, config: dict) -> HDRResult:
        result = HDRResult(algorithm_name=self.name)
        merge_config = config.get("raw_domain_weighted_merge", config.get("weighted_merge", {}))
        low = float(merge_config.get("low_threshold", 0.01))
        high = float(merge_config.get("high_threshold", 0.98))
        eps = float(merge_config.get("epsilon", 1e-8))

        with timed() as timer:
            shape = scene_data.frames[0].raw_mosaic.shape
            numerator, denominator, fallback_sum = init_accumulators(shape)
            weight_min = np.inf
            weight_max = 0.0
            weight_sum_total = 0.0
            weight_count = 0

            for frame, exposure_time in zip(scene_data.frames, scene_data.exposure_times):
                raw = sanitize_float_image(frame.raw_mosaic)
                radiance = raw / max(float(exposure_time), 1e-12)
                weights = triangular_weights(raw, low, high)
                numerator += weights * radiance
                denominator += weights
                fallback_sum += radiance
                weight_min = min(weight_min, float(np.min(weights)))
                weight_max = max(weight_max, float(np.max(weights)))
                weight_sum_total += float(np.sum(weights))
                weight_count += int(weights.size)

            raw_radiance = finalize_weighted_average(numerator, denominator, fallback_sum, len(scene_data.frames), eps)
            raw_radiance = sanitize_float_image(raw_radiance).astype(np.float32)

            cfa_pattern = scene_data.frames[0].cfa_pattern or ("R", "G", "G", "B")
            wb_gains = _white_balance_gains(scene_data)
            camera_rgb_hdr = _raw_radiance_to_rgb(raw_radiance, cfa_pattern, wb_gains)
            color_matrix, color_info = _estimate_scene_color_correction(scene_data, cfa_pattern, wb_gains, merge_config)
            hdr = _apply_color_matrix(camera_rgb_hdr, color_matrix)
            hdr, highlight_info = _repair_highlight_chroma(hdr, scene_data, merge_config)
            hdr, shadow_info = _repair_shadow_chroma(hdr, scene_data, merge_config)
            hdr = sanitize_float_image(hdr).astype(np.float32)

            finalize_hdr_result(result, hdr, config)
            result.metadata.update(
                {
                    "merge_mode": "streaming_raw_domain_weighted_average",
                    "raw_domain": True,
                    "raw_merge_domain": "black_corrected_white_normalized_mosaic",
                    "raw_demosaic": "bilinear_float_after_hdr_merge" if raw_radiance.ndim == 2 else "packed_raw_planes_to_rgb",
                    "raw_color_space": "linear_srgb_after_scene_color_correction",
                    "raw_color_correction": color_info,
                    "raw_highlight_chroma_repair": highlight_info,
                    "raw_shadow_chroma_repair": shadow_info,
                    "cfa_pattern": list(cfa_pattern),
                    "weight_min": 0.0 if not np.isfinite(weight_min) else weight_min,
                    "weight_max": weight_max,
                    "weight_mean": weight_sum_total / max(weight_count, 1),
                    "zero_weight_ratio": float(np.mean(denominator <= eps)),
                    "raw_radiance_min": float(np.min(raw_radiance)),
                    "raw_radiance_max": float(np.max(raw_radiance)),
                    "raw_radiance_mean": float(np.mean(raw_radiance)),
                }
            )
        result.runtime_seconds = timer.elapsed
        return result


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
    merge_config: dict,
) -> tuple[np.ndarray, dict]:
    method = str(merge_config.get("color_correction", "reference_fit")).lower()
    if method == "identity":
        return np.eye(3, dtype=np.float32), {"status": "identity_configured"}

    ref_idx = int(scene_data.alignment_info.get("reference_index", len(scene_data.frames) // 2))
    ref_frame = scene_data.frames[ref_idx]
    source = _raw_radiance_to_rgb(ref_frame.raw_mosaic, cfa_pattern, wb_gains)
    target = sanitize_float_image(ref_frame.linear_rgb)

    source_samples, target_samples = _sample_color_fit_pixels(
        source,
        target,
        max_samples=int(merge_config.get("color_fit_max_samples", 50000)),
        luma_low=float(merge_config.get("color_fit_luma_low", 0.02)),
        luma_high=float(merge_config.get("color_fit_luma_high", 0.90)),
    )
    if source_samples.shape[0] < 256:
        return np.eye(3, dtype=np.float32), {
            "status": "identity_insufficient_samples",
            "reference_file": ref_frame.metadata.filename,
            "sample_count": int(source_samples.shape[0]),
        }

    ridge = float(merge_config.get("color_fit_ridge", 1e-4))
    matrix = _ridge_fit_matrix(source_samples, target_samples, ridge)
    matrix = matrix.astype(np.float32)
    return matrix, {
        "status": "ridge_fit_to_rawpy_linear_srgb",
        "reference_file": ref_frame.metadata.filename,
        "sample_count": int(source_samples.shape[0]),
        "ridge": ridge,
        "matrix": matrix.tolist(),
    }


def _sample_color_fit_pixels(
    source: np.ndarray,
    target: np.ndarray,
    max_samples: int,
    luma_low: float,
    luma_high: float,
) -> tuple[np.ndarray, np.ndarray]:
    source = sanitize_float_image(source)
    target = sanitize_float_image(target)
    h, w = target.shape[:2]
    stride = max(1, int(np.sqrt(max(h * w / max(max_samples, 1), 1))))
    source = source[::stride, ::stride]
    target = target[::stride, ::stride]
    target_luminance = 0.2126 * target[..., 0] + 0.7152 * target[..., 1] + 0.0722 * target[..., 2]
    source_luminance = 0.2126 * source[..., 0] + 0.7152 * source[..., 1] + 0.0722 * source[..., 2]
    mask = (
        np.isfinite(source).all(axis=-1)
        & np.isfinite(target).all(axis=-1)
        & (target_luminance > luma_low)
        & (target_luminance < luma_high)
        & (source_luminance > 1e-6)
        & (np.max(source, axis=-1) > 1e-6)
        & (np.max(source, axis=-1) < 0.98)
    )
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return np.empty((0, 3), dtype=np.float32), np.empty((0, 3), dtype=np.float32)

    if ys.size > max_samples:
        sample_stride = max(1, ys.size // max_samples)
        ys = ys[::sample_stride]
        xs = xs[::sample_stride]
    return source[ys, xs].reshape(-1, 3), target[ys, xs].reshape(-1, 3)


def _ridge_fit_matrix(source_samples: np.ndarray, target_samples: np.ndarray, ridge: float) -> np.ndarray:
    xtx = source_samples.T @ source_samples
    xty = source_samples.T @ target_samples
    xtx += np.eye(3, dtype=np.float32) * max(ridge, 0.0)
    try:
        return np.linalg.solve(xtx, xty)
    except np.linalg.LinAlgError:
        matrix, *_ = np.linalg.lstsq(source_samples, target_samples, rcond=None)
        return matrix


def _apply_color_matrix(image: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    converted = image.reshape(-1, 3) @ matrix
    converted = converted.reshape(image.shape)
    return np.maximum(converted, 0.0).astype(np.float32)


def _repair_highlight_chroma(
    hdr: np.ndarray,
    scene_data: SceneData,
    merge_config: dict,
) -> tuple[np.ndarray, dict]:
    repair_config = merge_config.get("highlight_chroma_repair", {})
    if isinstance(repair_config, bool):
        enabled = repair_config
        repair_config = {}
    else:
        enabled = bool(repair_config.get("enabled", True))
    if not enabled:
        return hdr, {"enabled": False, "status": "disabled"}

    y = luminance(hdr)
    max_channel = np.max(hdr, axis=-1)
    positive = y[np.isfinite(y) & (y > 0)]
    positive_channel = max_channel[np.isfinite(max_channel) & (max_channel > 0)]
    if positive.size == 0 or positive_channel.size == 0:
        return hdr, {"enabled": True, "status": "skipped_no_positive_luminance"}

    percentile = float(repair_config.get("luminance_percentile", 99.75))
    saturation_threshold = float(repair_config.get("saturation_threshold", 0.18))
    blend_strength = float(repair_config.get("blend_strength", 0.85))
    target_saturation_limit = float(repair_config.get("target_saturation_limit", 0.12))
    min_blend = float(repair_config.get("min_blend", 0.70))
    low = float(repair_config.get("linear_weight_low", 0.01))
    high = float(repair_config.get("linear_weight_high", 0.98))

    threshold = float(np.percentile(positive, np.clip(percentile, 0.0, 100.0)))
    channel_threshold = float(np.percentile(positive_channel, np.clip(percentile, 0.0, 100.0)))
    y_scale = np.clip((y - threshold) / max(float(np.percentile(positive, 99.95)) - threshold, 1e-8), 0.0, 1.0)
    channel_scale = np.clip(
        (max_channel - channel_threshold)
        / max(float(np.percentile(positive_channel, 99.95)) - channel_threshold, 1e-8),
        0.0,
        1.0,
    )
    highlight_scale = np.maximum(y_scale, channel_scale)
    high_mask = (y >= threshold) | (max_channel >= channel_threshold)
    mask = np.zeros(y.shape, dtype=bool)
    high_y, high_x = np.nonzero(high_mask)
    if high_y.size:
        high_saturation = _rgb_saturation(hdr[high_y, high_x])
        selected = high_saturation >= saturation_threshold
        mask[high_y[selected], high_x[selected]] = True
    if not np.any(mask):
        return hdr, {
            "enabled": True,
            "status": "skipped_no_highlight_chroma_outliers",
            "luminance_percentile": percentile,
            "luminance_threshold": threshold,
            "max_channel_threshold": channel_threshold,
            "saturation_threshold": saturation_threshold,
        }

    reference = _best_linear_reference_radiance_for_mask(scene_data, mask, low, high)
    reference_y = luminance(reference)
    y_mask = y[mask]
    repaired = y_mask[:, None] * reference / np.maximum(reference_y[:, None], 1e-8)

    # If all linear references are saturated/invalid, fall back to neutral luminance.
    invalid_reference = reference_y <= 1e-8
    if np.any(invalid_reference):
        repaired[invalid_reference] = y_mask[invalid_reference, None]
    repaired = _limit_highlight_saturation(repaired, y_mask, target_saturation_limit)

    alpha = blend_strength * np.maximum(highlight_scale[mask], min_blend)
    output = hdr.copy()
    output[mask] = hdr[mask] * (1.0 - alpha[:, None]) + repaired * alpha[:, None]
    return np.maximum(output, 0.0).astype(np.float32), {
        "enabled": True,
        "status": "applied",
        "luminance_percentile": percentile,
        "luminance_threshold": threshold,
        "max_channel_threshold": channel_threshold,
        "saturation_threshold": saturation_threshold,
        "blend_strength": blend_strength,
        "target_saturation_limit": target_saturation_limit,
        "min_blend": min_blend,
        "affected_pixel_ratio": float(np.mean(mask)),
    }


def _repair_shadow_chroma(
    hdr: np.ndarray,
    scene_data: SceneData,
    merge_config: dict,
) -> tuple[np.ndarray, dict]:
    repair_config = merge_config.get("shadow_chroma_repair", {})
    if isinstance(repair_config, bool):
        enabled = repair_config
        repair_config = {}
    else:
        enabled = bool(repair_config.get("enabled", True))
    if not enabled:
        return hdr, {"enabled": False, "status": "disabled"}

    y = luminance(hdr)
    positive = y[np.isfinite(y) & (y > 0)]
    if positive.size == 0:
        return hdr, {"enabled": True, "status": "skipped_no_positive_luminance"}

    percentile = float(repair_config.get("luminance_percentile", 2.0))
    saturation_threshold = float(repair_config.get("saturation_threshold", 0.55))
    blend_strength = float(repair_config.get("blend_strength", 0.45))
    target_saturation_limit = float(repair_config.get("target_saturation_limit", 0.35))
    low = float(repair_config.get("linear_weight_low", 0.01))
    high = float(repair_config.get("linear_weight_high", 0.98))

    threshold = float(np.percentile(positive, np.clip(percentile, 0.0, 100.0)))
    candidate = (y > 1e-8) & (y <= threshold)
    mask = np.zeros(y.shape, dtype=bool)
    shadow_y, shadow_x = np.nonzero(candidate)
    if shadow_y.size:
        shadow_saturation = _rgb_saturation(hdr[shadow_y, shadow_x])
        selected = shadow_saturation >= saturation_threshold
        mask[shadow_y[selected], shadow_x[selected]] = True
    if not np.any(mask):
        return hdr, {
            "enabled": True,
            "status": "skipped_no_shadow_chroma_outliers",
            "luminance_percentile": percentile,
            "luminance_threshold": threshold,
            "saturation_threshold": saturation_threshold,
        }

    reference = _best_linear_reference_radiance_for_mask(scene_data, mask, low, high)
    reference_y = luminance(reference)
    y_mask = y[mask]
    repaired = y_mask[:, None] * reference / np.maximum(reference_y[:, None], 1e-8)
    invalid_reference = reference_y <= 1e-8
    if np.any(invalid_reference):
        repaired[invalid_reference] = y_mask[invalid_reference, None]
    repaired = _limit_highlight_saturation(repaired, y_mask, target_saturation_limit)

    darkness = 1.0 - np.clip(y_mask / max(threshold, 1e-8), 0.0, 1.0)
    alpha = blend_strength * darkness
    output = hdr.copy()
    output[mask] = hdr[mask] * (1.0 - alpha[:, None]) + repaired * alpha[:, None]
    return np.maximum(output, 0.0).astype(np.float32), {
        "enabled": True,
        "status": "applied",
        "luminance_percentile": percentile,
        "luminance_threshold": threshold,
        "saturation_threshold": saturation_threshold,
        "blend_strength": blend_strength,
        "target_saturation_limit": target_saturation_limit,
        "affected_pixel_ratio": float(np.mean(mask)),
    }


def _best_linear_reference_radiance_for_mask(
    scene_data: SceneData,
    mask: np.ndarray,
    low: float,
    high: float,
) -> np.ndarray:
    y_indices, x_indices = np.nonzero(mask)
    best_weight = np.zeros(y_indices.shape[0], dtype=np.float32)
    best_rgb = np.zeros((y_indices.shape[0], 3), dtype=np.float32)
    for frame, exposure_time in zip(scene_data.frames, scene_data.exposure_times):
        image = sanitize_float_image(frame.linear_rgb)
        pixels = image[y_indices, x_indices]
        lum = luminance(pixels)
        weight = triangular_weights(lum, low, high)
        update = weight > best_weight
        if np.any(update):
            radiance = pixels / max(float(exposure_time), 1e-12)
            best_rgb[update] = radiance[update]
            best_weight[update] = weight[update]
    return best_rgb


def _rgb_saturation(rgb: np.ndarray) -> np.ndarray:
    max_channel = np.max(rgb, axis=-1)
    min_channel = np.min(rgb, axis=-1)
    return (max_channel - min_channel) / np.maximum(max_channel, 1e-8)


def _limit_highlight_saturation(rgb: np.ndarray, y: np.ndarray, saturation_limit: float) -> np.ndarray:
    saturation = _rgb_saturation(rgb)
    neutral = np.repeat(y[..., None], 3, axis=-1)
    excess = np.clip((saturation - saturation_limit) / max(1.0 - saturation_limit, 1e-8), 0.0, 1.0)
    return rgb * (1.0 - excess[..., None]) + neutral * excess[..., None]


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
