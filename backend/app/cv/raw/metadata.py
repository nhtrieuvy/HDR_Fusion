from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RawMetadata:
    filename: str
    raw_format: str | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    lens_model: str | None = None
    width: int | None = None
    height: int | None = None
    iso: float | None = None
    aperture: float | None = None
    exposure_time: float | None = None
    exposure_bias: float | None = None
    focal_length: float | None = None
    black_level: Any | None = None
    white_level: float | None = None
    cfa_pattern: Any | None = None
    color_desc: str | None = None
    raw_channel_labels: list[str] | None = None
    color_matrix: Any | None = None
    camera_wb: Any | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def read_raw_metadata(path: Path) -> RawMetadata:
    meta = RawMetadata(filename=path.name, raw_format=path.suffix.lower().lstrip(".") or None)
    if path.suffix.lower() == ".npy":
        import numpy as np

        arr = np.load(path)
        meta.height, meta.width = arr.shape[:2]
        meta.white_level = 1.0
        meta.black_level = [0, 0, 0, 0]
        meta.cfa_pattern = ["R", "G", "G", "B"]
        meta.color_desc = "RGGB"
        meta.raw_channel_labels = ["R", "G", "G", "B"]
        meta.warnings.append("synthetic_npy_input")
        return meta
    try:
        import rawpy

        with rawpy.imread(str(path)) as raw:
            visible = raw.raw_image_visible
            meta.height, meta.width = visible.shape[:2]
            meta.black_level = [float(v) for v in getattr(raw, "black_level_per_channel", [])]
            meta.white_level = float(getattr(raw, "white_level", 0) or 0)
            meta.camera_wb = [float(v) for v in getattr(raw, "camera_whitebalance", [])]
            meta.color_desc = _read_color_desc(raw)
            meta.cfa_pattern = _read_cfa(raw)
            meta.raw_channel_labels = _read_raw_channel_labels(raw, visible.shape[-1] if visible.ndim == 3 else None, meta.color_desc)
            try:
                meta.color_matrix = raw.rgb_xyz_matrix.tolist()
            except Exception:
                meta.color_matrix = None
    except Exception as exc:
        meta.errors.append(f"rawpy_metadata_failed: {exc}")
    return meta


def _read_cfa(raw) -> list[str] | None:
    try:
        color_desc = _read_color_desc(raw)
        if not color_desc:
            return None
        if raw.raw_pattern is None:
            return None
        return [color_desc[int(index)] for index in raw.raw_pattern.flatten()]
    except Exception:
        return None


def _read_color_desc(raw) -> str | None:
    try:
        color_desc = raw.color_desc
        if isinstance(color_desc, bytes):
            return color_desc.decode("ascii")
        return str(color_desc)
    except Exception:
        return None


def _read_raw_channel_labels(raw, channel_count: int | None, color_desc: str | None) -> list[str] | None:
    if not channel_count:
        return None
    if raw.raw_pattern is not None:
        cfa = _read_cfa(raw)
        if cfa and len(cfa) >= channel_count:
            return cfa[:channel_count]
    if color_desc:
        labels = [str(ch).upper()[:1] for ch in color_desc[:channel_count]]
        if len(labels) == channel_count and set(labels).issubset({"R", "G", "B", "C", "M", "Y"}):
            return labels
    return None
