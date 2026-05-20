from __future__ import annotations

from pathlib import Path

import cv2
import imageio.v3 as iio
import numpy as np


DISPLAY_NAMES = {
    "linear_rgb_merge": "Linear RGB HDR Merge",
    "weighted_linear_rgb_merge": "Weighted Linear RGB HDR Merge",
    "noise_aware_weighted_linear_hdr_merge": "Noise-Aware Weighted Linear HDR Merge",
    "raw_domain_weighted_hdr_merge": "RAW-domain Weighted HDR Merge",
}


def create_contact_sheet(previews: dict[str, np.ndarray], output_path: Path) -> None:
    if not previews:
        return
    tile_w, tile_h = 480, 320
    label_h = 40
    canvas = np.full((2 * (tile_h + label_h), 2 * tile_w, 3), 245, dtype=np.uint8)
    order = [
        "linear_rgb_merge",
        "weighted_linear_rgb_merge",
        "noise_aware_weighted_linear_hdr_merge",
        "raw_domain_weighted_hdr_merge",
    ]

    for index, name in enumerate(order):
        row, col = divmod(index, 2)
        y0 = row * (tile_h + label_h)
        x0 = col * tile_w
        _put_label(canvas, DISPLAY_NAMES.get(name, name), x0 + 14, y0 + 27, tile_w - 28)
        if name not in previews:
            cv2.putText(
                canvas,
                "FAILED / NOT RUN",
                (x0 + 120, y0 + label_h + tile_h // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (120, 120, 120),
                2,
                cv2.LINE_AA,
            )
            continue
        image = previews[name]
        resized = _letterbox(image, tile_w, tile_h)
        canvas[y0 + label_h : y0 + label_h + tile_h, x0 : x0 + tile_w] = resized

    output_path.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(output_path, canvas)


def _letterbox(image: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = min(width / max(w, 1), height / max(h, 1))
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    tile = np.zeros((height, width, 3), dtype=np.uint8)
    y = (height - new_h) // 2
    x = (width - new_w) // 2
    tile[y : y + new_h, x : x + new_w] = resized
    return tile


def _put_label(canvas: np.ndarray, text: str, x: int, y: int, max_width: int) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.65
    thickness = 2
    while scale > 0.42:
        width = cv2.getTextSize(text, font, scale, thickness)[0][0]
        if width <= max_width:
            break
        scale -= 0.04
    cv2.putText(canvas, text, (x, y), font, scale, (20, 20, 20), thickness, cv2.LINE_AA)
