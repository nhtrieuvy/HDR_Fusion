from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import numpy as np


@dataclass(slots=True)
class RawMetadata:
    path: Path
    filename: str
    extension: str
    decoder: str = "rawpy/libraw"
    camera_model: str | None = None
    make: str | None = None
    exposure_time: float | None = None
    iso: float | None = None
    aperture: float | None = None
    focal_length: float | None = None
    white_balance: tuple[float, ...] | None = None
    black_level: tuple[float, ...] | None = None
    white_level: float | None = None
    raw_size: tuple[int, int] | None = None
    active_size: tuple[int, int] | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    exif: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RawFrame:
    metadata: RawMetadata
    raw_mosaic: np.ndarray
    cfa_pattern: tuple[str, str, str, str] | None
    linear_rgb: np.ndarray
    rendered_ldr: np.ndarray
    preview_rgb: np.ndarray


@dataclass(slots=True)
class SceneData:
    name: str
    folder: Path
    frames: list[RawFrame]
    exposure_times: np.ndarray
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    alignment_info: dict[str, Any] = field(default_factory=dict)

    @property
    def input_files(self) -> list[str]:
        return [str(frame.metadata.path) for frame in self.frames]

    @property
    def image_size(self) -> tuple[int, int]:
        h, w = self.frames[0].linear_rgb.shape[:2]
        return (w, h)


@dataclass(slots=True)
class HDRResult:
    algorithm_name: str
    hdr_radiance_map: np.ndarray | None = None
    preview_png: np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    runtime_seconds: float = 0.0
    hdr_output_path: Path | None = None
    preview_output_path: Path | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    status: str = "success"
    response_curve: np.ndarray | None = None


class HDRAlgorithm(Protocol):
    name: str

    def reconstruct(self, scene_data: SceneData, config: dict[str, Any]) -> HDRResult:
        ...
