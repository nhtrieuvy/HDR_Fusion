import io
import json

import numpy as np
import pytest

from app.cv.demosaic import external_amaze_service
from app.cv.demosaic.amaze_adapter import demosaic_amaze_or_fallback


def _npz_response(rgb: np.ndarray, metrics: dict[str, object] | None = None) -> bytes:
    buffer = io.BytesIO()
    np.savez_compressed(
        buffer,
        linear_rgb=rgb.astype(np.float32),
        metrics_json=np.asarray(json.dumps(metrics or {"external_method": "amaze"}), dtype=np.str_),
    )
    return buffer.getvalue()


def test_external_amaze_service_backend_success(monkeypatch):
    requested: dict[str, object] = {}
    rgb = np.ones((8, 10, 3), dtype=np.float32) * np.array([0.2, 0.3, 0.4], dtype=np.float32)

    class FakeResponse:
        content = _npz_response(rgb)

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, timeout):
            requested["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def post(self, url, content, headers):
            requested["url"] = url
            requested["headers"] = headers
            with np.load(io.BytesIO(content), allow_pickle=False) as payload:
                requested["mosaic_shape"] = tuple(payload["mosaic"].shape)
            return FakeResponse()

    monkeypatch.setattr(external_amaze_service.httpx, "Client", FakeClient)

    mosaic = np.full((8, 10), 0.25, dtype=np.float32)
    result = demosaic_amaze_or_fallback(
        mosaic,
        cfa_pattern=("R", "G", "G", "B"),
        demosaic_backend="external_amaze_service",
        amaze_service_url="http://amaze.local:8077",
        amaze_timeout_seconds=12,
        amaze_allow_fallback=False,
    )

    assert result.method == "external_amaze_service"
    assert result.rgb.shape == (8, 10, 3)
    assert result.metrics["demosaic_method"] == "external_amaze_service"
    assert result.metrics["amaze_fallback_used"] is False
    assert requested["url"] == "http://amaze.local:8077/v1/demosaic/amaze"
    assert requested["timeout"] == 12
    assert requested["mosaic_shape"] == (8, 10)


def test_external_amaze_service_fail_fast_when_fallback_disabled():
    mosaic = np.full((8, 10), 0.25, dtype=np.float32)

    with pytest.raises(RuntimeError, match="fallback is disabled"):
        demosaic_amaze_or_fallback(
            mosaic,
            demosaic_backend="external_amaze_service",
            amaze_service_url=None,
            amaze_allow_fallback=False,
        )


def test_external_amaze_service_falls_back_when_allowed():
    mosaic = np.full((8, 10), 0.25, dtype=np.float32)

    result = demosaic_amaze_or_fallback(
        mosaic,
        cfa_pattern=("R", "G", "G", "B"),
        demosaic_backend="external_amaze_service",
        amaze_service_url=None,
        amaze_allow_fallback=True,
    )

    assert result.method == "opencv_edge_aware_fallback"
    assert result.metrics["amaze_fallback_used"] is True
    assert "AMAZE_SERVICE_URL is required" in result.metrics["amaze_fallback_reason"]
