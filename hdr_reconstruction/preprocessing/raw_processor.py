from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import rawpy

from hdr_reconstruction.hdr.base import RawFrame
from hdr_reconstruction.io.raw_loader import read_raw_metadata
from hdr_reconstruction.utils.image_utils import resize_to_match


class RawProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.raw_config = config.get("raw", {})

    def load_frame(self, path: Path, exposure_override: float | None = None) -> RawFrame:
        metadata = read_raw_metadata(path, exposure_override)
        if metadata.errors:
            raise RuntimeError("; ".join(metadata.errors))

        with rawpy.imread(str(path)) as raw:
            raw_mosaic = self._read_normalized_raw_mosaic(raw)
            cfa_pattern = self._read_cfa_pattern(raw)
            linear_rgb = self._postprocess_linear(raw)
            rendered_ldr = self._postprocess_rendered_ldr(raw)

        target_shape = linear_rgb.shape[:2]
        rendered_ldr = resize_to_match(rendered_ldr, target_shape)
        preview_rgb = rendered_ldr.copy()
        raw_mosaic = resize_to_match(raw_mosaic, target_shape)
        return RawFrame(
            metadata=metadata,
            raw_mosaic=raw_mosaic,
            cfa_pattern=cfa_pattern,
            linear_rgb=linear_rgb,
            rendered_ldr=rendered_ldr,
            preview_rgb=preview_rgb,
        )

    def _postprocess_linear(self, raw: rawpy.RawPy) -> np.ndarray:
        # rawpy applies black subtraction, demosaic, white balance, and color conversion here.
        rgb16 = raw.postprocess(
            use_camera_wb=bool(self.raw_config.get("use_camera_wb", True)),
            no_auto_bright=True,
            output_bps=16,
            gamma=(1, 1),
            output_color=rawpy.ColorSpace.sRGB,
            demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
            user_flip=0,
            noise_thr=None if not self.raw_config.get("denoise", False) else 100,
        )
        linear = rgb16.astype(np.float32) / 65535.0
        return np.clip(linear, 0.0, 1.0)

    def _postprocess_rendered_ldr(self, raw: rawpy.RawPy) -> np.ndarray:
        rgb8 = raw.postprocess(
            use_camera_wb=bool(self.raw_config.get("use_camera_wb", True)),
            no_auto_bright=False,
            output_bps=8,
            gamma=(2.222, 4.5),
            output_color=rawpy.ColorSpace.sRGB,
            demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
            user_flip=0,
        )
        if self.raw_config.get("sharpen", False):
            blurred = cv2.GaussianBlur(rgb8, (0, 0), 0.8)
            rgb8 = cv2.addWeighted(rgb8, 1.4, blurred, -0.4, 0)
        return rgb8.astype(np.uint8)

    def load_scene_frames(self, files: list[Path], exposure_overrides: list[float | None]) -> list[RawFrame]:
        frames: list[RawFrame] = []
        for path, exposure in zip(files, exposure_overrides):
            frames.append(self.load_frame(path, exposure))
        return frames

    def _read_normalized_raw_mosaic(self, raw: rawpy.RawPy) -> np.ndarray:
        """Read visible RAW mosaic as black-corrected, white-normalized float32."""
        raw_image = raw.raw_image_visible.astype(np.float32).copy()
        black_level = float(np.mean(raw.black_level_per_channel))
        if self.raw_config.get("apply_black_level_correction", True):
            raw_image = np.maximum(raw_image - black_level, 0.0)
        if self.raw_config.get("apply_white_level_normalization", True) and raw.white_level:
            denom = max(float(raw.white_level) - black_level, 1.0)
            raw_image = raw_image / denom
        return np.clip(raw_image, 0.0, 1.0).astype(np.float32)

    def _read_cfa_pattern(self, raw: rawpy.RawPy) -> tuple[str, str, str, str] | None:
        try:
            color_desc = raw.color_desc.decode("ascii")
            if raw.raw_pattern is None:
                raw_image = raw.raw_image_visible
                if raw_image.ndim == 3 and raw_image.shape[-1] <= len(color_desc):
                    return tuple(color_desc[: raw_image.shape[-1]])
                return None
            pattern = tuple(color_desc[int(index)] for index in raw.raw_pattern.flatten())
            return pattern if len(pattern) == 4 else None
        except Exception:
            return None

    def read_raw_sensor_data(self, path: Path) -> np.ndarray:
        """Read the visible RAW mosaic as float32 for debugging or future sensor-space methods."""
        with rawpy.imread(str(path)) as raw:
            return self._read_normalized_raw_mosaic(raw)
