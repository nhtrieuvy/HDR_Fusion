from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

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
            frames = processor.load_scene_frames(scene_input.files, scene_input.exposure_overrides)
            scene_data = build_scene_data(
                scene_input.name,
                scene_input.folder,
                frames,
                scene_input.warnings,
                scene_input.errors,
                config,
            )

            if scene_data.errors:
                logger.error("Scene %s failed validation: %s", scene_data.name, "; ".join(scene_data.errors))
                write_scene_summary(output_root, scene_data, [])
                if not config.get("debug", {}).get("continue_on_scene_error", True):
                    return 1
                continue

            scene_data = align_scene(scene_data, config)
            if config.get("debug", {}).get("save_intermediate_preview", True):
                write_intermediate_previews(output_root, scene_data)
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
                create_contact_sheet(previews, output_root / scene_data.name / "comparison_contact_sheet.png")
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
