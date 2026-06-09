from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameExposure:
    index: int
    exposure_time: float | None = None
    iso: float | None = None
    aperture: float | None = None
    exposure_bias: float | None = None
    measured_luminance: float | None = None


def exposure_value(frame: FrameExposure) -> float:
    if frame.exposure_time and frame.exposure_time > 0:
        iso = frame.iso or 100.0
        aperture = frame.aperture or 1.0
        bias = frame.exposure_bias or 0.0
        return float(frame.exposure_time * iso / 100.0 / max(aperture * aperture, 1e-6) * (2.0**bias))
    if frame.measured_luminance is not None:
        return float(frame.measured_luminance)
    return float(frame.index + 1)


def sort_dark_to_bright(frames: list[FrameExposure]) -> list[int]:
    return [item.index for item in sorted(frames, key=exposure_value)]


def relative_exposure_ratios(frames: list[FrameExposure], reference_index: int) -> dict[int, float]:
    values = {frame.index: exposure_value(frame) for frame in frames}
    ref = max(values.get(reference_index, 1.0), 1e-8)
    return {index: max(value / ref, 1e-8) for index, value in values.items()}

