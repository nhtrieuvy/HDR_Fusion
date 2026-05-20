from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np

from hdr_reconstruction.hdr.base import RawFrame, SceneData


def _values_differ(values: Iterable[float | None], rtol: float = 1e-3) -> bool:
    numbers = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if len(numbers) < 2:
        return False
    return not np.allclose(numbers, numbers[0], rtol=rtol, atol=rtol)


def _strings_differ(values: Iterable[str | None]) -> bool:
    strings = [str(v).strip() for v in values if v]
    return len(set(strings)) > 1


def validate_frames(scene_name: str, frames: list[RawFrame], config: dict) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    input_config = config.get("input", {})
    min_images = int(input_config.get("min_images", 2))

    if len(frames) < min_images:
        errors.append(f"ERROR: Scene {scene_name} has fewer than {min_images} valid RAW images")
    if len(frames) > int(input_config.get("warn_if_more_than", 9)):
        warnings.append(f"WARNING: More than {input_config.get('warn_if_more_than', 9)} images in {scene_name}")
    if len(frames) < int(input_config.get("recommended_min_images", 3)):
        warnings.append(f"WARNING: Fewer than recommended images in {scene_name}")
    if len(frames) > int(input_config.get("recommended_max_images", 7)):
        warnings.append(f"WARNING: More than recommended images in {scene_name}")

    exposures = [frame.metadata.exposure_time for frame in frames]
    for frame in frames:
        t = frame.metadata.exposure_time
        if t is None:
            errors.append(f"ERROR: Missing exposure time for {frame.metadata.filename}")
        elif not math.isfinite(float(t)) or float(t) <= 0:
            errors.append(f"ERROR: Invalid exposure time for {frame.metadata.filename}: {t}")

    valid_exposures = [float(t) for t in exposures if t is not None and float(t) > 0]
    if len(valid_exposures) >= 2 and np.ptp(valid_exposures) <= max(1e-9, 0.01 * max(valid_exposures)):
        errors.append("ERROR: Exposure times are not sufficiently different")

    shapes = [frame.linear_rgb.shape[:2] for frame in frames]
    if len(set(shapes)) > 1:
        errors.append("ERROR: Image dimensions mismatch")

    active_sizes = [frame.metadata.active_size for frame in frames if frame.metadata.active_size]
    if len(set(active_sizes)) > 1:
        errors.append("ERROR: RAW active area dimensions mismatch")

    mosaic_shapes = [frame.raw_mosaic.shape[:2] for frame in frames]
    if len(set(mosaic_shapes)) > 1:
        errors.append("ERROR: RAW mosaic dimensions mismatch")

    cfa_patterns = [frame.cfa_pattern for frame in frames if frame.cfa_pattern]
    if len(set(cfa_patterns)) > 1:
        errors.append("ERROR: CFA/Bayer pattern mismatch")

    if _strings_differ(frame.metadata.camera_model for frame in frames):
        warnings.append("WARNING: Camera model differs between frames")
    if _values_differ(frame.metadata.iso for frame in frames):
        warnings.append("WARNING: ISO differs between frames")
    if _values_differ(frame.metadata.aperture for frame in frames):
        warnings.append("WARNING: Aperture differs between frames")
    if _values_differ(frame.metadata.focal_length for frame in frames):
        warnings.append("WARNING: Focal length differs between frames")

    wbs = [frame.metadata.white_balance for frame in frames if frame.metadata.white_balance]
    if len({tuple(round(float(x), 4) for x in wb) for wb in wbs}) > 1:
        warnings.append("WARNING: White balance metadata differs between frames")

    return warnings, errors


def build_scene_data(scene_name: str, folder, frames: list[RawFrame], warnings: list[str], errors: list[str], config: dict) -> SceneData:
    validation_warnings, validation_errors = validate_frames(scene_name, frames, config)
    warnings = [*warnings, *validation_warnings]
    errors = [*errors, *validation_errors]
    exposure_times = np.array([float(frame.metadata.exposure_time or 0.0) for frame in frames], dtype=np.float32)
    return SceneData(scene_name, folder, frames, exposure_times, warnings, errors)
