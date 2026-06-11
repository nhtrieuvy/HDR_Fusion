from __future__ import annotations

import io
import json
from dataclasses import dataclass
from typing import Any

import numpy as np


class AmazeContractError(ValueError):
    pass


@dataclass(frozen=True)
class AmazeRequest:
    mosaic: np.ndarray
    meta: dict[str, Any]


@dataclass(frozen=True)
class AmazeResponse:
    linear_rgb: np.ndarray
    metrics: dict[str, Any]


def decode_request_npz(content: bytes) -> AmazeRequest:
    try:
        with np.load(io.BytesIO(content), allow_pickle=False) as data:
            if "mosaic" not in data:
                raise AmazeContractError("request missing mosaic array")
            if "meta_json" not in data:
                raise AmazeContractError("request missing meta_json")
            mosaic = data["mosaic"].astype(np.float32)
            meta = json.loads(str(data["meta_json"].item()))
    except AmazeContractError:
        raise
    except Exception as exc:
        raise AmazeContractError(f"request is not a valid npz payload: {exc}") from exc
    validate_request(mosaic, meta)
    return AmazeRequest(mosaic=mosaic, meta=meta)


def encode_response_npz(response: AmazeResponse) -> bytes:
    validate_response(response.linear_rgb)
    metrics = dict(response.metrics)
    buffer = io.BytesIO()
    np.savez_compressed(
        buffer,
        linear_rgb=response.linear_rgb.astype(np.float32, copy=False),
        metrics_json=np.asarray(json.dumps(metrics), dtype=np.str_),
    )
    return buffer.getvalue()


def validate_request(mosaic: np.ndarray, meta: dict[str, Any]) -> None:
    if mosaic.ndim != 2:
        raise AmazeContractError(f"mosaic must be 2D Bayer data, got shape={mosaic.shape}")
    if mosaic.size == 0:
        raise AmazeContractError("mosaic is empty")
    if not np.all(np.isfinite(mosaic)):
        raise AmazeContractError("mosaic contains non-finite values")
    if float(np.max(mosaic)) <= 1e-8:
        raise AmazeContractError("mosaic is effectively black")
    cfa = meta.get("cfa_pattern")
    if not isinstance(cfa, (list, tuple)) or len(cfa) != 4:
        raise AmazeContractError("meta_json.cfa_pattern must contain 4 CFA labels")
    if any(str(item).upper()[:1] not in {"R", "G", "B"} for item in cfa):
        raise AmazeContractError("meta_json.cfa_pattern contains invalid labels")


def validate_response(linear_rgb: np.ndarray) -> None:
    if linear_rgb.ndim != 3 or linear_rgb.shape[-1] != 3:
        raise AmazeContractError(f"linear_rgb must be HxWx3 float32, got shape={linear_rgb.shape}")
    if linear_rgb.size == 0:
        raise AmazeContractError("linear_rgb is empty")
    if not np.all(np.isfinite(linear_rgb)):
        raise AmazeContractError("linear_rgb contains non-finite values")
    if float(np.max(linear_rgb)) <= 1e-8:
        raise AmazeContractError("linear_rgb is effectively black")
    if float(np.percentile(linear_rgb, 99.9)) > 32.0:
        raise AmazeContractError("linear_rgb scale is unexpectedly high")
