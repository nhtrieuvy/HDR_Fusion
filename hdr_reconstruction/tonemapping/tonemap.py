from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(slots=True)
class ToneMapResult:
    image: np.ndarray
    metadata: dict[str, Any]


def tone_map_preview(
    hdr: np.ndarray,
    config: dict,
    exposure: float | None = None,
) -> np.ndarray:
    return tone_map_with_metadata(hdr, config, exposure=exposure).image


def tone_map_with_metadata(
    hdr: np.ndarray,
    config: dict,
    exposure: float | None = None,
) -> ToneMapResult:
    tonemap_config = config.get("tonemapping", {})
    method = str(tonemap_config.get("method", "aces_filmic")).lower()
    gamma = float(tonemap_config.get("gamma", 2.2))
    base_exposure = float(tonemap_config.get("exposure", 1.0))
    effective_exposure = base_exposure if exposure is None else float(exposure)
    percentile_enabled = bool(tonemap_config.get("percentile_normalization", True))
    percentile_black = float(tonemap_config.get("percentile_black", 0.1))
    percentile_white = float(tonemap_config.get("percentile_white", 99.7))
    preserve_color = bool(tonemap_config.get("preserve_color", True))
    reinhard_white = float(tonemap_config.get("reinhard_white", 4.0))
    shadow_lift = float(tonemap_config.get("shadow_lift", 0.0))

    has_nan = bool(np.isnan(hdr).any())
    has_inf = bool(np.isinf(hdr).any())
    clean = np.asarray(hdr, dtype=np.float32)
    clean = np.nan_to_num(clean, nan=0.0, posinf=0.0, neginf=0.0)
    clean = np.maximum(clean, 0.0) * effective_exposure
    normalized, norm_info = _percentile_normalize(
        clean,
        enabled=percentile_enabled,
        percentile_black=percentile_black,
        percentile_white=percentile_white,
        preserve_color=preserve_color,
    )

    if preserve_color:
        mapped_linear = _tone_map_preserve_color(normalized, method, reinhard_white)
    else:
        mapped_linear = _apply_operator(normalized, method, reinhard_white)

    mapped_linear = np.clip(np.nan_to_num(mapped_linear, nan=0.0, posinf=1.0, neginf=0.0), 0.0, 1.0)
    if shadow_lift > 0:
        mapped_linear = _lift_shadows(mapped_linear, shadow_lift)
    gamma_corrected = np.power(mapped_linear, 1.0 / max(gamma, 1e-8))
    image = (np.clip(gamma_corrected, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)

    metadata: dict[str, Any] = {
        "method": method,
        "exposure": effective_exposure,
        "gamma": gamma,
        "percentile_normalization": percentile_enabled,
        "percentile_black": percentile_black,
        "percentile_white": percentile_white,
        "preserve_color": preserve_color,
        "shadow_lift": shadow_lift,
        "has_nan": has_nan,
        "has_inf": has_inf,
        **norm_info,
    }
    return ToneMapResult(image=image, metadata=metadata)


def _percentile_normalize(
    hdr: np.ndarray,
    enabled: bool,
    percentile_black: float,
    percentile_white: float,
    preserve_color: bool,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not enabled or not np.any(hdr > 0):
        return hdr, {
            "normalization_black_value": None,
            "normalization_white_value": None,
        }

    luminance = _luminance(hdr)
    samples = luminance[np.isfinite(luminance) & (luminance > 0)]
    if samples.size == 0:
        return hdr, {
            "normalization_black_value": None,
            "normalization_white_value": None,
        }

    black = float(np.percentile(samples, np.clip(percentile_black, 0.0, 100.0)))
    white = float(np.percentile(samples, np.clip(percentile_white, 0.0, 100.0)))
    if white <= black:
        white = black + 1e-8
    if preserve_color and hdr.ndim == 3:
        y_norm = np.maximum((luminance - black) / (white - black), 0.0)
        scale = y_norm / np.maximum(luminance, 1e-8)
        normalized = hdr * scale[..., None]
    else:
        normalized = np.maximum((hdr - black) / (white - black), 0.0)
    return normalized.astype(np.float32), {
        "normalization_black_value": black,
        "normalization_white_value": white,
    }


def _tone_map_preserve_color(hdr: np.ndarray, method: str, reinhard_white: float) -> np.ndarray:
    y = _luminance(hdr)
    y_mapped = _apply_operator(y, method, reinhard_white)
    scale = y_mapped / np.maximum(y, 1e-8)
    return hdr * scale[..., None]


def _apply_operator(values: np.ndarray, method: str, reinhard_white: float) -> np.ndarray:
    x = np.maximum(values.astype(np.float32), 0.0)
    if method == "simple_global":
        return x / (1.0 + x)
    if method == "reinhard":
        white2 = max(reinhard_white * reinhard_white, 1e-8)
        return (x * (1.0 + x / white2)) / (1.0 + x)
    if method == "aces_filmic":
        return _aces_filmic(x)
    raise ValueError(f"Unsupported tone mapping method: {method}")


def _aces_filmic(values: np.ndarray) -> np.ndarray:
    a = 2.51
    b = 0.03
    c = 2.43
    d = 0.59
    e = 0.14
    return (values * (a * values + b)) / (values * (c * values + d) + e)


def _lift_shadows(values: np.ndarray, amount: float) -> np.ndarray:
    strength = np.clip(amount, 0.0, 0.25)
    lift = np.sqrt(np.clip(values, 0.0, 1.0)) - values
    return np.clip(values + strength * lift, 0.0, 1.0)


def _luminance(rgb: np.ndarray) -> np.ndarray:
    if rgb.ndim == 2:
        return rgb.astype(np.float32)
    return (
        0.2126 * rgb[..., 0]
        + 0.7152 * rgb[..., 1]
        + 0.0722 * rgb[..., 2]
    ).astype(np.float32)
