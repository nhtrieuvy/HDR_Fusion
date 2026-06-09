from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_pipeline_version():
    client = TestClient(app)
    response = client.get("/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["pipeline_name"] == "raw_hdr_fusion"

