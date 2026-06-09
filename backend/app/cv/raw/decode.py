from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.cv.raw.black_white import normalize_raw_mosaic
from app.cv.raw.cfa import normalize_cfa_pattern
from app.cv.raw.metadata import RawMetadata, read_raw_metadata
from app.cv.demosaic.amaze_adapter import multichannel_raw_to_rgb


@dataclass
class DecodedRawFrame:
    path: Path
    metadata: RawMetadata
    raw_mosaic: np.ndarray
    linear_proxy_rgb: np.ndarray
    rendered_preview_rgb: np.ndarray
    cfa_pattern: tuple[str, str, str, str]
    raw_channel_labels: tuple[str, ...] | None
    stats: dict[str, Any]


def decode_raw_frame(path: Path) -> DecodedRawFrame:
    if path.suffix.lower() == ".npy":
        return _decode_npy(path)
    import rawpy

    metadata = read_raw_metadata(path)
    if metadata.errors:
        raise RuntimeError("; ".join(metadata.errors))
    with rawpy.imread(str(path)) as raw:
        normalized = normalize_raw_mosaic(raw.raw_image_visible.copy(), raw.black_level_per_channel, raw.white_level)
        rgb16 = raw.postprocess(
            use_camera_wb=True,
            no_auto_bright=True,
            output_bps=16,
            gamma=(1, 1),
            output_color=rawpy.ColorSpace.sRGB,
            demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
            user_flip=0,
        )
        proxy = rgb16.astype(np.float32) / 65535.0
        preview8 = raw.postprocess(
            use_camera_wb=True,
            no_auto_bright=False,
            output_bps=8,
            gamma=(2.222, 4.5),
            output_color=rawpy.ColorSpace.sRGB,
            demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
            user_flip=0,
        )
        cfa = normalize_cfa_pattern(metadata.cfa_pattern)
        channel_labels = _normalize_channel_labels(metadata.raw_channel_labels, normalized.mosaic.shape[-1] if normalized.mosaic.ndim == 3 else None)
    return DecodedRawFrame(path, metadata, normalized.mosaic, proxy, preview8, cfa, channel_labels, normalized.metrics)


def _decode_npy(path: Path) -> DecodedRawFrame:
    arr = np.load(path).astype(np.float32)
    if arr.ndim == 3:
        mosaic = arr
        channel_labels = ("R", "G", "G", "B") if arr.shape[-1] == 4 else None
        proxy = np.clip(multichannel_raw_to_rgb(arr, channel_labels), 0.0, 1.0)
    else:
        mosaic = arr
        channel_labels = None
        proxy = np.repeat(np.clip(arr, 0.0, 1.0)[..., None], 3, axis=-1)
    metadata = read_raw_metadata(path)
    normalized = normalize_raw_mosaic(mosaic, metadata.black_level, metadata.white_level)
    preview = (np.clip(proxy, 0.0, 1.0) ** (1 / 2.2) * 255.0).astype(np.uint8)
    return DecodedRawFrame(path, metadata, normalized.mosaic, proxy.astype(np.float32), preview, ("R", "G", "G", "B"), channel_labels, normalized.metrics)


def _normalize_channel_labels(labels: Any, channel_count: int | None) -> tuple[str, ...] | None:
    if not labels or not channel_count:
        return None
    values = tuple(str(item).upper()[:1] for item in labels[:channel_count])
    if len(values) == channel_count and set(values).issubset({"R", "G", "B", "C", "M", "Y"}):
        return values
    return None
