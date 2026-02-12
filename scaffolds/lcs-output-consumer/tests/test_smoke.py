from fastapi.testclient import TestClient

from lcs_output_consumer.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] in {"ok", "degraded"}
