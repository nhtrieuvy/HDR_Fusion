#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np


class EngineError(RuntimeError):
    pass


def main() -> None:
    parser = argparse.ArgumentParser(description="HDR Fusion RawTherapee AMaZE engine.")
    parser.add_argument("input_npz", help="Input npz containing mosaic and meta_json")
    parser.add_argument("output_npz", help="Output npz to write linear_rgb and metrics_json")
    parser.add_argument("--rawtherapee-cli", default=os.getenv("RAWTHERAPEE_CLI", ""), help="Path to rawtherapee-cli")
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    started = time.perf_counter()
    request = _load_input(Path(args.input_npz))
    executable = _resolve_rawtherapee_cli(args.rawtherapee_cli)
    with tempfile.TemporaryDirectory(prefix="hdr-rt-amaze-") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        dng_path = _write_synthetic_dng(request["mosaic"], request["meta"], temp_dir)
        pp3_path = _write_rawtherapee_profile(temp_dir)
        tif_path = temp_dir / "amaze_output.tif"
        command = [
            executable,
            "-o",
            str(tif_path),
            "-t",
            "-Y",
            "-p",
            str(pp3_path),
            "-c",
            str(dng_path),
        ]
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=float(os.getenv("RAWTHERAPEE_TIMEOUT_SECONDS", "180")),
        )
        if completed.returncode != 0:
            raise EngineError(f"rawtherapee-cli failed with exit code {completed.returncode}: {completed.stderr.strip()[-4000:]}")
        produced = _find_rawtherapee_output(tif_path, temp_dir)
        rgb_raw = _read_tiff_as_linear_rgb(produced)
        rgb, shape_metrics = _match_shape_to_mosaic(rgb_raw, request["mosaic"].shape)
        metrics = {
            "native_engine": "rawtherapee_cli_amaze_synthetic_dng",
            "native_engine_runtime_seconds": float(time.perf_counter() - started),
            "rawtherapee_cli": executable,
            "rawtherapee_output": produced.name,
            "dng_shape": list(request["mosaic"].shape),
            "rawtherapee_rgb_shape": list(rgb_raw.shape),
            **shape_metrics,
            "cfa_pattern": request["meta"].get("cfa_pattern"),
            "output_transfer_assumption": "srgb_tiff_inverse_transfer_to_linear",
            "stdout_tail": completed.stdout.strip()[-1000:],
            "stderr_tail": completed.stderr.strip()[-1000:],
        }
        _write_output(Path(args.output_npz), rgb, metrics)
        if args.keep_temp:
            keep_dir = Path(args.output_npz).with_suffix(".debug")
            keep_dir.mkdir(parents=True, exist_ok=True)
            for item in temp_dir.iterdir():
                shutil.copy2(item, keep_dir / item.name)


def _load_input(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise EngineError(f"input npz does not exist: {path}")
    with np.load(path, allow_pickle=False) as data:
        if "mosaic" not in data:
            raise EngineError("input npz missing mosaic")
        if "meta_json" not in data:
            raise EngineError("input npz missing meta_json")
        mosaic = data["mosaic"].astype(np.float32)
        meta = json.loads(str(data["meta_json"].item()))
    if mosaic.ndim != 2:
        raise EngineError(f"RawTherapee AMaZE engine requires 2D Bayer mosaic, got {mosaic.shape}")
    if not np.all(np.isfinite(mosaic)):
        raise EngineError("mosaic contains non-finite values")
    if float(np.max(mosaic)) <= 1e-8:
        raise EngineError("mosaic is effectively black")
    return {"mosaic": np.clip(mosaic, 0.0, 1.0), "meta": meta}


def _resolve_rawtherapee_cli(configured: str) -> str:
    candidates = [configured] if configured else []
    candidates.extend(["rawtherapee-cli", "rawtherapee"])
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if resolved:
            return resolved
    raise EngineError(
        "rawtherapee-cli not found. Install it in WSL/Linux with: sudo apt install -y rawtherapee"
    )


def _write_synthetic_dng(mosaic: np.ndarray, meta: dict[str, Any], output_dir: Path) -> Path:
    try:
        from pidng.camdefs import CFAPattern, DNGTags, Tag
        from pidng.core import RAW2DNG
    except Exception as exc:
        raise EngineError(
            "PiDNG is required to create synthetic DNG. Install in WSL/Linux with: pip install PiDNG"
        ) from exc

    h, w = mosaic.shape
    data16 = np.clip(mosaic * 65535.0, 0.0, 65535.0).astype(np.uint16)
    cfa_pattern = _cfa_pattern(meta.get("cfa_pattern"))
    cfa_value = {
        "RGGB": CFAPattern.RGGB,
        "BGGR": CFAPattern.BGGR,
        "GRBG": CFAPattern.GRBG,
        "GBRG": CFAPattern.GBRG,
    }[cfa_pattern]

    tags = DNGTags()
    rationals = lambda values: [[int(num), int(den)] for num, den in values]
    _set_tags(
        tags,
        [
            (Tag.ImageWidth, w),
            (Tag.ImageLength, h),
            (Tag.TileWidth, w),
            (Tag.TileLength, h),
            (Tag.Orientation, 1),
            (Tag.PhotometricInterpretation, 32803),
            (Tag.SamplesPerPixel, 1),
            (Tag.BitsPerSample, 16),
            (Tag.CFARepeatPatternDim, [2, 2]),
            (Tag.CFAPattern, cfa_value),
            (Tag.BlackLevel, [0]),
            (Tag.WhiteLevel, [65535]),
            (Tag.Make, "HDRFusion"),
            (Tag.Model, "MergedBayer"),
            (Tag.DNGVersion, [1, 4, 0, 0]),
            (Tag.DNGBackwardVersion, [1, 1, 0, 0]),
            (Tag.ColorMatrix1, rationals([(1, 1), (0, 1), (0, 1), (0, 1), (1, 1), (0, 1), (0, 1), (0, 1), (1, 1)])),
            (Tag.AsShotNeutral, rationals([(1, 1), (1, 1), (1, 1)])),
        ],
    )
    converter = RAW2DNG()
    converter.options(tags, str(output_dir), compress=False)
    return Path(converter.convert(data16, "merged_bayer_amaze_input"))


def _set_tags(tags: Any, items: list[tuple[Any, Any]]) -> None:
    for tag, value in items:
        tags.set(tag, value)


def _cfa_pattern(value: Any) -> str:
    labels = value if isinstance(value, (list, tuple)) else ["R", "G", "G", "B"]
    pattern = "".join(str(item).upper()[:1] for item in labels)
    if pattern not in {"RGGB", "BGGR", "GRBG", "GBRG"}:
        raise EngineError(f"unsupported CFA pattern for AMaZE engine: {pattern}")
    return pattern


def _write_rawtherapee_profile(output_dir: Path) -> Path:
    profile = output_dir / "amaze_neutral.pp3"
    profile.write_text(
        "\n".join(
            [
                "[Version]",
                "AppVersion=5.10",
                "Version=351",
                "",
                "[RAW]",
                "Method=amaze",
                "Border=4",
                "",
                "[Exposure]",
                "Auto=false",
                "Clip=0",
                "Compensation=0",
                "Brightness=0",
                "Contrast=0",
                "Saturation=0",
                "",
                "[Sharpening]",
                "Enabled=false",
                "",
                "[Color Management]",
                "InputProfile=(camera)",
                "WorkingProfile=ProPhoto",
                "OutputProfile=RT_sRGB",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return profile


def _find_rawtherapee_output(expected: Path, temp_dir: Path) -> Path:
    if expected.exists():
        return expected
    candidates = sorted(temp_dir.glob("*.tif")) + sorted(temp_dir.glob("*.tiff"))
    if candidates:
        return candidates[0]
    raise EngineError("rawtherapee-cli completed but no TIFF output was produced")


def _read_tiff_as_linear_rgb(path: Path) -> np.ndarray:
    image = imageio.imread(path)
    data = np.asarray(image)
    if data.ndim == 2:
        data = np.repeat(data[..., None], 3, axis=-1)
    if data.ndim != 3 or data.shape[-1] < 3:
        raise EngineError(f"RawTherapee TIFF output must be RGB, got shape={data.shape}")
    data = data[..., :3]
    if data.dtype == np.uint8:
        rgb = data.astype(np.float32) / 255.0
    elif data.dtype == np.uint16:
        rgb = data.astype(np.float32) / 65535.0
    else:
        rgb = data.astype(np.float32)
        if float(np.nanmax(rgb)) > 2.0:
            rgb = rgb / max(float(np.nanmax(rgb)), 1.0)
    return _srgb_to_linear(np.clip(rgb, 0.0, 1.0)).astype(np.float32)


def _match_shape_to_mosaic(rgb: np.ndarray, target_shape: tuple[int, int]) -> tuple[np.ndarray, dict[str, Any]]:
    target_h, target_w = int(target_shape[0]), int(target_shape[1])
    h, w = rgb.shape[:2]
    metrics: dict[str, Any] = {
        "shape_restoration_applied": False,
        "shape_restoration_method": "none",
    }
    if (h, w) == (target_h, target_w):
        return rgb.astype(np.float32), metrics
    if h <= target_h and w <= target_w:
        pad_top = (target_h - h) // 2
        pad_bottom = target_h - h - pad_top
        pad_left = (target_w - w) // 2
        pad_right = target_w - w - pad_left
        restored = np.pad(rgb, ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)), mode="edge")
        metrics.update(
            {
                "shape_restoration_applied": True,
                "shape_restoration_method": "edge_pad_after_rawtherapee_border_crop",
                "shape_restoration_padding": [pad_top, pad_bottom, pad_left, pad_right],
            }
        )
        return restored.astype(np.float32), metrics
    cropped = rgb[:target_h, :target_w, :]
    metrics.update(
        {
            "shape_restoration_applied": True,
            "shape_restoration_method": "top_left_crop_to_mosaic_shape",
            "shape_restoration_crop_from": [h, w],
        }
    )
    return cropped.astype(np.float32), metrics


def _srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    low = rgb <= 0.04045
    return np.where(low, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def _write_output(path: Path, rgb: np.ndarray, metrics: dict[str, Any]) -> None:
    if rgb.ndim != 3 or rgb.shape[-1] != 3:
        raise EngineError(f"linear_rgb must be HxWx3, got {rgb.shape}")
    if not np.all(np.isfinite(rgb)):
        raise EngineError("linear_rgb contains non-finite values")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        linear_rgb=rgb.astype(np.float32),
        metrics_json=np.asarray(json.dumps(metrics), dtype=np.str_),
    )


if __name__ == "__main__":
    try:
        main()
    except EngineError as exc:
        raise SystemExit(f"rawtherapee_amaze_engine_error: {exc}") from exc
