from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from app.cv.raw.metadata import RawMetadata, read_raw_metadata


@dataclass
class BracketAuditResult:
    status: str
    metadata: list[RawMetadata]
    metrics: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def audit_raw_files(paths: list[Path], min_frames: int = 3, max_frames: int = 7) -> BracketAuditResult:
    warnings: list[str] = []
    errors: list[str] = []
    metadata = [read_raw_metadata(path) for path in paths]
    for item in metadata:
        warnings.extend(f"{item.filename}: {warning}" for warning in item.warnings)
        errors.extend(f"{item.filename}: {error}" for error in item.errors)
    if len(paths) < min_frames:
        errors.append(f"Need at least {min_frames} RAW files, got {len(paths)}")
    if len(paths) > max_frames:
        warnings.append(f"Expected at most {max_frames} RAW files, got {len(paths)}")

    dims = {(item.width, item.height) for item in metadata if item.width and item.height}
    if len(dims) > 1:
        errors.append(f"Incompatible RAW dimensions: {sorted(dims)}")

    cameras = {item.camera_model for item in metadata if item.camera_model}
    if len(cameras) > 1:
        warnings.append(f"Mixed camera models: {sorted(cameras)}")

    apertures = [item.aperture for item in metadata if item.aperture]
    if len(apertures) > 1 and np.nanmax(apertures) - np.nanmin(apertures) > 0.1:
        warnings.append("Aperture mismatch across bracket")

    exposures = [item.exposure_time for item in metadata]
    missing_exif = sum(value is None for value in exposures)
    if missing_exif:
        warnings.append(f"{missing_exif} frame(s) missing exposure_time metadata")

    metrics = {
        "frame_count": len(paths),
        "dimensions": [list(dim) for dim in sorted(dims)] if dims else [],
        "exposure_times": [float(v) if v is not None else None for v in exposures],
        "missing_exposure_count": missing_exif,
        "camera_models": sorted(cameras),
        "apertures": [float(v) for v in apertures],
        "audit_warning_count": len(warnings),
        "audit_error_count": len(errors),
    }
    status = "fail" if errors else ("warn" if warnings else "pass")
    return BracketAuditResult(status, metadata, metrics, warnings, errors)

