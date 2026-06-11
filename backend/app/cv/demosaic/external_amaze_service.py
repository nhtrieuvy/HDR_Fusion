from __future__ import annotations

import io
import json
from dataclasses import dataclass
from typing import Any

import httpx
import numpy as np


class ExternalAmazeServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExternalAmazeServiceResult:
    rgb: np.ndarray
    metrics: dict[str, Any]


def demosaic_with_external_amaze_service(
    mosaic: np.ndarray,
    *,
    service_url: str | None,
    timeout_seconds: float,
    cfa_pattern: tuple[str, str, str, str] | None,
    camera_wb: list[float] | tuple[float, ...] | None,
    color_desc: str | None,
) -> ExternalAmazeServiceResult:
    if not service_url:
        raise ExternalAmazeServiceError("AMAZE_SERVICE_URL is required when DEMOSAIC_BACKEND=external_amaze_service")
    if mosaic.ndim != 2:
        raise ExternalAmazeServiceError(f"external AMaZE requires a 2D Bayer mosaic, got shape={mosaic.shape}")

    endpoint = service_url.rstrip("/") + "/v1/demosaic/amaze"
    payload = _encode_request_payload(mosaic, cfa_pattern, camera_wb, color_desc)
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                endpoint,
                content=payload,
                headers={"content-type": "application/vnd.hdr-fusion.amaze+npz"},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ExternalAmazeServiceError(f"external AMaZE service request failed: {exc}") from exc

    result = _decode_response_payload(response.content)
    if result.rgb.shape[:2] != mosaic.shape[:2]:
        raise ExternalAmazeServiceError(
            f"external AMaZE returned shape {result.rgb.shape[:2]} for input mosaic shape {mosaic.shape[:2]}"
        )
    return result


def _encode_request_payload(
    mosaic: np.ndarray,
    cfa_pattern: tuple[str, str, str, str] | None,
    camera_wb: list[float] | tuple[float, ...] | None,
    color_desc: str | None,
) -> bytes:
    meta = {
        "contract_version": 1,
        "mosaic_shape": list(mosaic.shape),
        "mosaic_dtype": "float32",
        "cfa_pattern": list(cfa_pattern or ("R", "G", "G", "B")),
        "camera_wb": list(camera_wb) if camera_wb is not None else None,
        "color_desc": color_desc,
        "input_scale": "linear_float32_normalized_radiance",
        "expected_output": "linear_rgb_float32",
    }
    buffer = io.BytesIO()
    np.savez_compressed(
        buffer,
        mosaic=mosaic.astype(np.float32, copy=False),
        meta_json=np.asarray(json.dumps(meta), dtype=np.str_),
    )
    return buffer.getvalue()


def _decode_response_payload(content: bytes) -> ExternalAmazeServiceResult:
    try:
        with np.load(io.BytesIO(content), allow_pickle=False) as data:
            if "linear_rgb" not in data:
                raise ExternalAmazeServiceError("external AMaZE response missing linear_rgb array")
            rgb = data["linear_rgb"].astype(np.float32)
            metrics = _read_metrics(data)
    except ExternalAmazeServiceError:
        raise
    except Exception as exc:
        raise ExternalAmazeServiceError(f"external AMaZE response is not a valid npz payload: {exc}") from exc

    _validate_linear_rgb(rgb)
    metrics.update(
        {
            "demosaic_method": "external_amaze_service",
            "requested_demosaic_method": "AMAZE",
            "amaze_backend": "external_service",
            "amaze_fallback_used": False,
        }
    )
    return ExternalAmazeServiceResult(rgb=rgb, metrics=metrics)


def _read_metrics(data: Any) -> dict[str, Any]:
    if "metrics_json" not in data:
        return {}
    value = data["metrics_json"]
    raw = str(value.item() if hasattr(value, "item") else value)
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ExternalAmazeServiceError("external AMaZE metrics_json must decode to an object")
    return parsed


def _validate_linear_rgb(rgb: np.ndarray) -> None:
    if rgb.ndim != 3 or rgb.shape[-1] != 3:
        raise ExternalAmazeServiceError(f"external AMaZE linear_rgb must be HxWx3, got shape={rgb.shape}")
    if rgb.size == 0:
        raise ExternalAmazeServiceError("external AMaZE linear_rgb is empty")
    if not np.all(np.isfinite(rgb)):
        raise ExternalAmazeServiceError("external AMaZE linear_rgb contains non-finite values")
    if float(np.max(rgb)) <= 1e-7:
        raise ExternalAmazeServiceError("external AMaZE linear_rgb is effectively black")
    if float(np.percentile(rgb, 99.9)) > 32.0:
        raise ExternalAmazeServiceError("external AMaZE linear_rgb scale is unexpectedly high")
