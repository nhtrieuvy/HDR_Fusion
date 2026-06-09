from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
import numpy as np


def write_jpeg(image: np.ndarray, path: Path, quality: int = 92) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, image.astype(np.uint8), quality=quality)


def write_webp(image: np.ndarray, path: Path, quality: int = 90) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, image.astype(np.uint8), quality=quality)


def write_png(image: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, image.astype(np.uint8))


def write_tiff_float(image: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, image.astype(np.float32))
