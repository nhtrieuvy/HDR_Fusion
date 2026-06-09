from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass
class DemosaicResult:
    rgb: np.ndarray
    method: str
    metrics: dict[str, Any]


def demosaic_amaze_or_fallback(
    mosaic: np.ndarray,
    reference_raw_path: Path | None = None,
    cfa_pattern: tuple[str, str, str, str] | None = None,
    raw_channel_labels: tuple[str, ...] | None = None,
    camera_wb: list[float] | tuple[float, ...] | None = None,
    color_desc: str | None = None,
) -> DemosaicResult:
    if mosaic.ndim == 3:
        labels = raw_channel_labels or cfa_pattern
        rgb, channel_metrics = multichannel_raw_to_rgb_with_metrics(mosaic, labels)
        rgb, wb_metrics = apply_camera_white_balance_rgb(rgb, camera_wb, color_desc)
        metrics = _linear_rgb_metrics(
            rgb,
            {
                "demosaic_method": "multichannel_raw_to_linear_rgb",
                "requested_demosaic_method": "AMAZE",
                "amaze_fallback_reason": "input_is_multichannel_linear_dng_not_bayer_mosaic",
                "linear_raw_channel_count": int(mosaic.shape[-1]),
                **channel_metrics,
                **wb_metrics,
            },
        )
        return DemosaicResult(rgb.astype(np.float32), "multichannel_raw_to_linear_rgb", metrics)

    # Real AMaZE through LibRaw is file-based. For merged synthetic mosaic we use a strict adapter
    # with explicit fallback reason instead of silently claiming AMaZE.
    rgb = demosaic_bayer_opencv(mosaic, cfa_pattern)
    rgb, wb_metrics = apply_camera_white_balance_rgb(rgb, camera_wb, color_desc)
    metrics = _linear_rgb_metrics(rgb, {
        "demosaic_method": "opencv_edge_aware_fallback",
        "requested_demosaic_method": "AMAZE",
        "amaze_fallback_reason": "merged_raw_mosaic_array_requires_external_amaze_bridge",
        **wb_metrics,
    })
    return DemosaicResult(rgb.astype(np.float32), "opencv_edge_aware_fallback", metrics)


def demosaic_bayer_opencv(mosaic: np.ndarray, cfa_pattern: tuple[str, str, str, str] | None = None) -> np.ndarray:
    data = np.clip(mosaic.astype(np.float32), 0.0, 1.0)
    u16 = (data * 65535.0).astype(np.uint16)
    pattern = "".join(cfa_pattern or ("R", "G", "G", "B")).upper()
    code = cv2.COLOR_BAYER_RG2RGB_EA
    if pattern == "BGGR":
        code = cv2.COLOR_BAYER_BG2RGB_EA
    elif pattern == "GRBG":
        code = cv2.COLOR_BAYER_GR2RGB_EA
    elif pattern == "GBRG":
        code = cv2.COLOR_BAYER_GB2RGB_EA
    rgb = cv2.cvtColor(u16, code).astype(np.float32) / 65535.0
    return np.clip(rgb, 0.0, None)


def multichannel_raw_to_rgb(raw: np.ndarray, cfa_pattern: tuple[str, ...] | None = None) -> np.ndarray:
    rgb, _ = multichannel_raw_to_rgb_with_metrics(raw, cfa_pattern)
    return rgb


def multichannel_raw_to_rgb_with_metrics(raw: np.ndarray, cfa_pattern: tuple[str, ...] | None = None) -> tuple[np.ndarray, dict[str, Any]]:
    data = np.clip(raw.astype(np.float32), 0.0, None)
    channels = data.shape[-1]
    metrics: dict[str, Any] = {
        "raw_channel_labels_used": list(cfa_pattern or []),
        "ignored_raw_channels": [],
    }
    if channels == 1:
        return np.repeat(data, 3, axis=-1), metrics
    if channels == 2:
        return np.repeat(np.mean(data, axis=-1, keepdims=True), 3, axis=-1), metrics
    labels = list(cfa_pattern or ())
    if len(labels) == channels:
        sums = {name: np.zeros(data.shape[:2], dtype=np.float32) for name in ("R", "G", "B")}
        counts = {name: 0 for name in ("R", "G", "B")}
        for idx, label in enumerate(labels):
            key = str(label).upper()[:1]
            if _is_padding_or_empty_channel(data[..., idx]):
                metrics["ignored_raw_channels"].append({"index": idx, "label": key, "reason": "near_zero_padding_channel"})
                continue
            if key in sums:
                sums[key] += data[..., idx]
                counts[key] += 1
        if counts["R"] and counts["G"] and counts["B"]:
            rgb = np.stack(
                [
                    sums["R"] / counts["R"],
                    sums["G"] / counts["G"],
                    sums["B"] / counts["B"],
                ],
                axis=-1,
            )
            metrics["raw_channel_counts_used"] = counts
            return np.clip(rgb, 0.0, None), metrics
    metrics["raw_channel_fallback"] = "first_three_channels"
    return data[..., :3], metrics


def apply_camera_white_balance_rgb(
    rgb: np.ndarray,
    camera_wb: list[float] | tuple[float, ...] | None,
    color_desc: str | None,
) -> tuple[np.ndarray, dict[str, Any]]:
    gains = _rgb_gains_from_camera_wb(camera_wb, color_desc)
    if gains is None:
        return rgb, {"camera_white_balance_applied": False, "camera_white_balance_reason": "missing_or_invalid_camera_wb"}
    out = rgb.astype(np.float32) * gains.reshape((1, 1, 3))
    return np.clip(out, 0.0, None), {
        "camera_white_balance_applied": True,
        "camera_white_balance_gains": [float(v) for v in gains],
        "camera_white_balance_color_desc": color_desc,
    }


def _rgb_gains_from_camera_wb(
    camera_wb: list[float] | tuple[float, ...] | None,
    color_desc: str | None,
) -> np.ndarray | None:
    if not camera_wb:
        return None
    values = np.asarray(camera_wb, dtype=np.float32)
    if values.size < 3 or not np.any(values > 0):
        return None
    desc = (color_desc or "RGBG").upper()
    by_color: dict[str, list[float]] = {"R": [], "G": [], "B": []}
    for idx, gain in enumerate(values):
        if idx >= len(desc):
            break
        key = desc[idx : idx + 1]
        if key in by_color and np.isfinite(gain) and gain > 0:
            by_color[key].append(float(gain))
    if not by_color["R"] or not by_color["G"] or not by_color["B"]:
        if values.size >= 3 and np.all(np.isfinite(values[:3])) and np.all(values[:3] > 0):
            r_gain, g_gain, b_gain = values[:3]
        else:
            return None
    else:
        r_gain = float(np.mean(by_color["R"]))
        g_gain = float(np.mean(by_color["G"]))
        b_gain = float(np.mean(by_color["B"]))
    gains = np.asarray([r_gain / max(g_gain, 1e-6), 1.0, b_gain / max(g_gain, 1e-6)], dtype=np.float32)
    return np.clip(gains, 0.25, 4.0)


def _is_padding_or_empty_channel(channel: np.ndarray) -> bool:
    return float(np.percentile(channel, 99.9)) < 1e-5 and float(np.max(channel)) < 1e-4


def _linear_rgb_metrics(rgb: np.ndarray, base: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(base)
    metrics.update(
        {
            "linear_rgb_min": float(np.min(rgb)),
            "linear_rgb_max": float(np.max(rgb)),
            "linear_rgb_median": float(np.median(rgb)),
            "linear_rgb_p95": float(np.percentile(rgb, 95)),
            "linear_rgb_p99": float(np.percentile(rgb, 99)),
        }
    )
    return metrics
