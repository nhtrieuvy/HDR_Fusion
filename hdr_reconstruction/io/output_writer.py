from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

import cv2
import imageio.v3 as iio
import numpy as np

from hdr_reconstruction.hdr.base import HDRResult, SceneData
from hdr_reconstruction.utils.image_utils import hdr_statistics, rgb_to_bgr, sanitize_float_image


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return str(value)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=_json_default)


def write_algorithm_outputs(
    output_root: Path,
    scene_data: SceneData,
    result: HDRResult,
    config: dict | None = None,
) -> HDRResult:
    algorithm_dir = output_root / scene_data.name / result.algorithm_name
    algorithm_dir.mkdir(parents=True, exist_ok=True)
    write_start = perf_counter()
    hdr_path = algorithm_dir / "hdr.hdr"
    preview_path = algorithm_dir / "preview.png"
    response_path = algorithm_dir / "response_curve.npy"

    if result.hdr_radiance_map is not None and result.status == "success":
        hdr = sanitize_float_image(result.hdr_radiance_map).astype(np.float32)
        cv2.imwrite(str(hdr_path), rgb_to_bgr(hdr))
        result.hdr_output_path = hdr_path
        result.metadata.update(hdr_statistics(hdr))

    if result.preview_png is not None and result.status == "success":
        iio.imwrite(preview_path, result.preview_png.astype(np.uint8))
        result.preview_output_path = preview_path

    if result.response_curve is not None and result.status == "success":
        np.save(response_path, result.response_curve)
        result.metadata["response_curve_path"] = str(response_path)

    result.metadata["output_write_seconds"] = perf_counter() - write_start
    log_payload = build_algorithm_log(scene_data, result)
    write_json(algorithm_dir / "log.json", log_payload)
    return result


def build_algorithm_log(scene_data: SceneData, result: HDRResult) -> dict[str, Any]:
    first = scene_data.frames[0].metadata if scene_data.frames else None
    payload: dict[str, Any] = {
        "scene_name": scene_data.name,
        "algorithm_name": result.algorithm_name,
        "input_files": scene_data.input_files,
        "raw_format/file_extension": [frame.metadata.extension for frame in scene_data.frames],
        "camera_model": first.camera_model if first else None,
        "image_size": list(scene_data.image_size) if scene_data.frames else None,
        "raw_mosaic_size": list(scene_data.frames[0].raw_mosaic.shape[:2]) if scene_data.frames else None,
        "cfa_pattern": scene_data.frames[0].cfa_pattern if scene_data.frames else None,
        "exposure_times": scene_data.exposure_times.tolist(),
        "ISO": [frame.metadata.iso for frame in scene_data.frames],
        "aperture": [frame.metadata.aperture for frame in scene_data.frames],
        "focal_length": [frame.metadata.focal_length for frame in scene_data.frames],
        "white_balance": [frame.metadata.white_balance for frame in scene_data.frames],
        "validation_warnings": scene_data.warnings,
        "validation_errors": scene_data.errors,
        "alignment_method": scene_data.alignment_info,
        "alignment_status": scene_data.alignment_info.get("linear_status")
        or scene_data.alignment_info.get("classical_status"),
        "runtime_seconds": result.runtime_seconds,
        "preview_output_path": str(result.preview_output_path) if result.preview_output_path else None,
        "hdr_output_path": str(result.hdr_output_path) if result.hdr_output_path else None,
        "status": result.status,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    payload.update(result.metadata)
    return payload


def write_scene_summary(output_root: Path, scene_data: SceneData, results: list[HDRResult]) -> None:
    algorithms: dict[str, Any] = {}
    for result in results:
        algorithms[result.algorithm_name] = {
            "status": result.status,
            "runtime_seconds": result.runtime_seconds,
            "output_write_seconds": result.metadata.get("output_write_seconds"),
            "hdr_statistics": {
                key: result.metadata.get(key)
                for key in (
                    "hdr_min",
                    "hdr_max",
                    "hdr_mean",
                    "hdr_dynamic_range_estimate",
                    "clipping_ratio",
                    "nan_count",
                    "inf_count",
                )
            },
            "preview_output_path": str(result.preview_output_path) if result.preview_output_path else None,
            "hdr_output_path": str(result.hdr_output_path) if result.hdr_output_path else None,
            "warnings": result.warnings,
            "errors": result.errors,
        }

    summary = {
        "scene_name": scene_data.name,
        "num_images": len(scene_data.frames),
        "exposure_times": scene_data.exposure_times.tolist(),
        "algorithms": algorithms,
        "warnings": scene_data.warnings,
        "errors": scene_data.errors,
        "alignment_info": scene_data.alignment_info,
        "processing_info": scene_data.processing_info,
    }
    write_json(output_root / scene_data.name / "summary.json", summary)


def write_intermediate_previews(output_root: Path, scene_data: SceneData) -> None:
    debug_dir = output_root / scene_data.name / "debug" / "rendered_previews"
    debug_dir.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(scene_data.frames):
        stem = f"{index:02d}_{frame.metadata.path.stem}.png"
        iio.imwrite(debug_dir / stem, frame.preview_rgb.astype(np.uint8))


def write_scene_error_summary(output_root: Path, scene_name: str, warnings: list[str], errors: list[str]) -> None:
    summary = {
        "scene_name": scene_name,
        "num_images": 0,
        "exposure_times": [],
        "algorithms": {},
        "warnings": warnings,
        "errors": errors,
        "status": "fail",
    }
    write_json(output_root / scene_name / "summary.json", summary)
