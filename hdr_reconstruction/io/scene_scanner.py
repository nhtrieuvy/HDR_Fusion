from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from hdr_reconstruction.io.exposure_reader import override_for_scene
from hdr_reconstruction.io.raw_loader import can_open_raw, read_raw_metadata


@dataclass(slots=True)
class SceneInput:
    name: str
    folder: Path
    files: list[Path]
    exposure_overrides: list[float | None] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def discover_scene_folders(input_root: Path) -> list[Path]:
    if not input_root.exists():
        raise FileNotFoundError(f"Input root does not exist: {input_root}")
    return sorted([p for p in input_root.iterdir() if p.is_dir()], key=lambda p: p.name)


def scan_scene(scene_folder: Path, override_data: dict | None = None) -> SceneInput:
    scene_name = scene_folder.name
    warnings: list[str] = []
    errors: list[str] = []
    files: list[Path] = []
    exposure_overrides: list[float | None] = []
    scene_override = override_for_scene(scene_name, override_data or {})

    if scene_override:
        for image_name, exposure_time in zip(scene_override["images"], scene_override["exposure_times"]):
            path = scene_folder / image_name
            if not path.exists():
                errors.append(f"ERROR: Override image not found: {image_name}")
                continue
            ok, err = can_open_raw(path)
            if not ok:
                errors.append(f"ERROR: RAW decoder cannot open {image_name}: {err}")
                continue
            files.append(path)
            exposure_overrides.append(float(exposure_time))
        return SceneInput(scene_name, scene_folder, files, exposure_overrides, warnings, errors)

    candidates = sorted([p for p in scene_folder.iterdir() if p.is_file()], key=lambda p: p.name)
    raw_candidates: list[tuple[Path, float]] = []
    for path in candidates:
        ok, err = can_open_raw(path)
        if not ok:
            warnings.append(f"WARNING: RAW decoder cannot open {path.name}: {err}")
            continue
        metadata = read_raw_metadata(path)
        if metadata.exposure_time is None:
            errors.append(f"ERROR: Missing exposure time for {path.name}")
            continue
        raw_candidates.append((path, float(metadata.exposure_time)))

    raw_candidates.sort(key=lambda item: item[1])
    files = [item[0] for item in raw_candidates]
    exposure_overrides = [None for _ in files]
    return SceneInput(scene_name, scene_folder, files, exposure_overrides, warnings, errors)


def scan_input_root(input_root: Path, override_data: dict | None = None) -> list[SceneInput]:
    return [scan_scene(folder, override_data) for folder in discover_scene_folders(input_root)]

