import io
import json
import sys

import numpy as np
from fastapi.testclient import TestClient

from amaze_service import main
from amaze_service.settings import AmazeServiceSettings


def _request_payload() -> bytes:
    mosaic = np.full((8, 10), 0.25, dtype=np.float32)
    meta = {
        "contract_version": 1,
        "cfa_pattern": ["R", "G", "G", "B"],
        "mosaic_shape": [8, 10],
    }
    buffer = io.BytesIO()
    np.savez_compressed(
        buffer,
        mosaic=mosaic,
        meta_json=np.asarray(json.dumps(meta), dtype=np.str_),
    )
    return buffer.getvalue()


def test_amaze_service_returns_503_when_engine_is_not_configured(monkeypatch):
    monkeypatch.setattr(
        main,
        "settings",
        AmazeServiceSettings(engine_command=None, engine_timeout_seconds=20.0, max_request_bytes=10_000_000),
    )
    client = TestClient(main.app)

    response = client.post("/v1/demosaic/amaze", content=_request_payload())

    assert response.status_code == 503
    assert "AMAZE_ENGINE_COMMAND is not configured" in response.text


def test_amaze_service_runs_configured_engine(tmp_path, monkeypatch):
    engine_script = tmp_path / "fake_engine.py"
    engine_script.write_text(
        """
import json
import sys
import numpy as np

input_path, output_path = sys.argv[1], sys.argv[2]
with np.load(input_path, allow_pickle=False) as data:
    mosaic = data["mosaic"].astype(np.float32)
rgb = np.repeat(mosaic[..., None], 3, axis=-1)
np.savez_compressed(
    output_path,
    linear_rgb=rgb,
    metrics_json=np.asarray(json.dumps({"engine": "contract_test"}), dtype=np.str_),
)
""".strip(),
        encoding="utf-8",
    )
    command = f'"{sys.executable}" "{engine_script}" {{input}} {{output}}'
    monkeypatch.setattr(
        main,
        "settings",
        AmazeServiceSettings(engine_command=command, engine_timeout_seconds=20.0, max_request_bytes=10_000_000),
    )
    client = TestClient(main.app)

    response = client.post("/v1/demosaic/amaze", content=_request_payload())

    assert response.status_code == 200
    with np.load(io.BytesIO(response.content), allow_pickle=False) as data:
        assert data["linear_rgb"].shape == (8, 10, 3)
        metrics = json.loads(str(data["metrics_json"].item()))
    assert metrics["engine"] == "contract_test"
    assert metrics["amaze_service_engine_protocol"] == "npz_file_command_v1"
