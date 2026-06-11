from __future__ import annotations

import argparse
import io
import json

import httpx
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description="Check HDR Fusion external AMaZE service contract.")
    parser.add_argument("--url", default="http://127.0.0.1:8077", help="AMaZE service base URL")
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    with httpx.Client(timeout=args.timeout) as client:
        health = client.get(f"{base_url}/v1/health")
        print("health:", health.status_code, health.text)
        payload = _make_payload()
        response = client.post(
            f"{base_url}/v1/demosaic/amaze",
            content=payload,
            headers={"content-type": "application/vnd.hdr-fusion.amaze+npz"},
        )
        print("demosaic:", response.status_code)
        if response.status_code != 200:
            print(response.text)
            raise SystemExit(1)
        with np.load(io.BytesIO(response.content), allow_pickle=False) as data:
            rgb = data["linear_rgb"]
            metrics = json.loads(str(data["metrics_json"].item())) if "metrics_json" in data else {}
        print("linear_rgb_shape:", rgb.shape)
        print("linear_rgb_min_max:", float(np.min(rgb)), float(np.max(rgb)))
        print("metrics:", json.dumps(metrics, indent=2, sort_keys=True))


def _make_payload() -> bytes:
    h, w = 64, 96
    y = np.linspace(0.05, 0.9, h, dtype=np.float32)[:, None]
    x = np.linspace(0.05, 0.7, w, dtype=np.float32)[None, :]
    mosaic = np.clip((x + y) * 0.5, 0.0, 1.0).astype(np.float32)
    meta = {
        "contract_version": 1,
        "mosaic_shape": [h, w],
        "mosaic_dtype": "float32",
        "cfa_pattern": ["R", "G", "G", "B"],
        "camera_wb": [1.0, 1.0, 1.0, 1.0],
        "color_desc": "RGBG",
        "input_scale": "linear_float32_normalized_radiance",
        "expected_output": "linear_rgb_float32",
    }
    buffer = io.BytesIO()
    np.savez_compressed(
        buffer,
        mosaic=mosaic,
        meta_json=np.asarray(json.dumps(meta), dtype=np.str_),
    )
    return buffer.getvalue()


if __name__ == "__main__":
    main()
