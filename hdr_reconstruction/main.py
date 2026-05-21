from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from time import perf_counter

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from tqdm import tqdm

from hdr_reconstruction.config import load_config, load_exposure_override
from hdr_reconstruction.evaluation.contact_sheet import create_contact_sheet
from hdr_reconstruction.hdr.base import HDRResult
from hdr_reconstruction.hdr.registry import get_algorithms
from hdr_reconstruction.io.output_writer import (
    write_intermediate_previews,
    write_algorithm_outputs,
    write_scene_error_summary,
    write_scene_summary,
)
from hdr_reconstruction.io.scene_scanner import scan_input_root
from hdr_reconstruction.preprocessing.alignment import align_scene
from hdr_reconstruction.preprocessing.raw_processor import RawProcessor
from hdr_reconstruction.preprocessing.validation import build_scene_data
from hdr_reconstruction.utils.logger import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch HDR reconstruction from multiple camera RAW exposures.")
    parser.add_argument("--input", required=True, help="Input root folder containing one folder per scene.")
    parser.add_argument("--output", required=True, help="Output root folder.")
    parser.add_argument("--config", default=None, help="YAML config path. Defaults to configs/default.yaml.")
    parser.add_argument("--exposure-override", default=None, help="Optional exposure_override.json path.")
    parser.add_argument("--log-level", default="INFO", help="Python logging level.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_root = Path(args.input)
    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(args.log_level, output_root / "batch.log")

    try:
        config = load_config(args.config)
        override_data = load_exposure_override(args.exposure_override)
        scene_inputs = scan_input_root(input_root, override_data)
        algorithms = get_algorithms(config.get("hdr", {}).get("algorithms", []))
    except Exception as exc:
        logger.error("Failed to initialize pipeline: %s", exc)
        return 2

    processor = RawProcessor(config)
    for scene_input in tqdm(scene_inputs, desc="Scenes"):
        logger.info("Processing scene %s", scene_input.name)
        try:
            scene_start = perf_counter()
            load_start = perf_counter()
            frames = processor.load_scene_frames(scene_input.files, scene_input.exposure_overrides)
            load_seconds = perf_counter() - load_start

            validation_start = perf_counter()
            scene_data = build_scene_data(
                scene_input.name,
                scene_input.folder,
                frames,
                scene_input.warnings,
                scene_input.errors,
                config,
            )
            scene_data.processing_info["raw_load_seconds"] = load_seconds
            scene_data.processing_info["validation_seconds"] = perf_counter() - validation_start

            if scene_data.errors:
                logger.error("Scene %s failed validation: %s", scene_data.name, "; ".join(scene_data.errors))
                write_scene_summary(output_root, scene_data, [])
                if not config.get("debug", {}).get("continue_on_scene_error", True):
                    return 1
                continue

            alignment_start = perf_counter()
            scene_data = align_scene(scene_data, config)
            scene_data.processing_info["alignment_seconds"] = perf_counter() - alignment_start
            if config.get("debug", {}).get("save_intermediate_preview", True):
                debug_start = perf_counter()
                write_intermediate_previews(output_root, scene_data)
                scene_data.processing_info["intermediate_preview_seconds"] = perf_counter() - debug_start
            else:
                scene_data.processing_info["intermediate_preview_seconds"] = 0.0
            results: list[HDRResult] = []
            previews = {}

            for algorithm in algorithms:
                logger.info("[%s] Running %s", scene_data.name, algorithm.name)
                try:
                    result = algorithm.reconstruct(scene_data, config)
                except Exception as exc:
                    logger.error("[%s] Algorithm %s failed: %s", scene_data.name, algorithm.name, exc)
                    result = HDRResult(
                        algorithm_name=algorithm.name,
                        status="fail",
                        errors=[str(exc), traceback.format_exc()],
                    )
                    if not config.get("debug", {}).get("continue_on_algorithm_error", True):
                        write_algorithm_outputs(output_root, scene_data, result, config)
                        results.append(result)
                        write_scene_summary(output_root, scene_data, results)
                        return 1

                result = write_algorithm_outputs(output_root, scene_data, result, config)
                results.append(result)
                if result.status == "success" and result.preview_png is not None:
                    previews[result.algorithm_name] = result.preview_png

            if config.get("debug", {}).get("save_contact_sheet", True):
                contact_start = perf_counter()
                create_contact_sheet(previews, output_root / scene_data.name / "comparison_contact_sheet.png")
                scene_data.processing_info["contact_sheet_seconds"] = perf_counter() - contact_start
            else:
                scene_data.processing_info["contact_sheet_seconds"] = 0.0
            scene_data.processing_info["total_scene_seconds"] = perf_counter() - scene_start
            write_scene_summary(output_root, scene_data, results)
        except Exception as exc:
            logger.error("Scene %s failed unexpectedly: %s", scene_input.name, exc)
            errors = [*scene_input.errors, str(exc), traceback.format_exc()]
            write_scene_error_summary(output_root, scene_input.name, scene_input.warnings, errors)
            if not config.get("debug", {}).get("continue_on_scene_error", True):
                return 1

    logger.info("Batch complete. Output: %s", output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
