from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def write_mask_png(path: Path, mask: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, (np.clip(mask.astype(np.float32), 0, 1) * 255).astype(np.uint8))

