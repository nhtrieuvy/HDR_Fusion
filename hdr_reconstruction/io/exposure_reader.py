from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

import exifread


EXPOSURE_TAGS = ("EXIF ExposureTime", "Image ExposureTime")
ISO_TAGS = ("EXIF ISOSpeedRatings", "EXIF PhotographicSensitivity")
APERTURE_TAGS = ("EXIF FNumber", "EXIF ApertureValue")
FOCAL_LENGTH_TAGS = ("EXIF FocalLength",)
MODEL_TAGS = ("Image Model",)
MAKE_TAGS = ("Image Make",)


def _ratio_to_float(value: Any) -> float | None:
    try:
        if hasattr(value, "num") and hasattr(value, "den"):
            return float(value.num) / float(value.den)
        return float(Fraction(str(value)))
    except Exception:
        return None


def _first_tag(tags: dict[str, Any], names: tuple[str, ...]) -> Any | None:
    for name in names:
        if name in tags:
            value = tags[name]
            if getattr(value, "values", None):
                values = value.values
                return values[0] if isinstance(values, list) else values
            return value
    return None


def read_exif_metadata(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    try:
        with path.open("rb") as f:
            tags = exifread.process_file(f, details=False, strict=False)
    except Exception as exc:
        metadata["exif_error"] = str(exc)
        return metadata

    exposure = _first_tag(tags, EXPOSURE_TAGS)
    iso = _first_tag(tags, ISO_TAGS)
    aperture = _first_tag(tags, APERTURE_TAGS)
    focal_length = _first_tag(tags, FOCAL_LENGTH_TAGS)
    model = _first_tag(tags, MODEL_TAGS)
    make = _first_tag(tags, MAKE_TAGS)

    metadata["exposure_time"] = _ratio_to_float(exposure) if exposure is not None else None
    metadata["iso"] = _ratio_to_float(iso) if iso is not None else None
    metadata["aperture"] = _ratio_to_float(aperture) if aperture is not None else None
    metadata["focal_length"] = _ratio_to_float(focal_length) if focal_length is not None else None
    metadata["camera_model"] = str(model).strip() if model is not None else None
    metadata["make"] = str(make).strip() if make is not None else None
    metadata["raw_exif_tags"] = {k: str(v) for k, v in tags.items() if k.startswith(("EXIF", "Image"))}
    return metadata


def override_for_scene(scene_name: str, override_data: dict[str, Any]) -> dict[str, Any] | None:
    value = override_data.get(scene_name)
    if not value:
        return None
    images = value.get("images", [])
    times = value.get("exposure_times", [])
    if len(images) != len(times):
        raise ValueError(f"Exposure override for {scene_name} has mismatched images/exposure_times")
    return {"images": images, "exposure_times": [float(t) for t in times]}

