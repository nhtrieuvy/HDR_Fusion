from __future__ import annotations

from pathlib import Path

import rawpy

from hdr_reconstruction.hdr.base import RawMetadata
from hdr_reconstruction.io.exposure_reader import read_exif_metadata


def can_open_raw(path: Path) -> tuple[bool, str | None]:
    try:
        with rawpy.imread(str(path)):
            return True, None
    except Exception as exc:
        return False, str(exc)


def read_raw_metadata(path: Path, exposure_override: float | None = None) -> RawMetadata:
    exif = read_exif_metadata(path)
    metadata = RawMetadata(
        path=path,
        filename=path.name,
        extension=path.suffix.lower(),
        camera_model=exif.get("camera_model"),
        make=exif.get("make"),
        exposure_time=exposure_override if exposure_override is not None else exif.get("exposure_time"),
        iso=exif.get("iso"),
        aperture=exif.get("aperture"),
        focal_length=exif.get("focal_length"),
        exif=exif.get("raw_exif_tags", {}),
    )

    try:
        with rawpy.imread(str(path)) as raw:
            metadata.white_balance = tuple(float(x) for x in raw.camera_whitebalance)
            metadata.black_level = tuple(float(x) for x in raw.black_level_per_channel)
            metadata.white_level = float(raw.white_level) if raw.white_level is not None else None
            sizes = raw.sizes
            metadata.raw_size = (int(sizes.raw_width), int(sizes.raw_height))
            metadata.active_size = (int(sizes.width), int(sizes.height))
    except Exception as exc:
        metadata.errors.append(f"RAW decoder cannot open {path.name}: {exc}")

    if exposure_override is not None:
        metadata.exif["exposure_source"] = "override"
    else:
        metadata.exif["exposure_source"] = "metadata"
    return metadata

