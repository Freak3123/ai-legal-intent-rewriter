"""Health endpoint smoke tests."""

from fastapi.testclient import TestClient


def test_root_returns_service_info(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "AI Legal Intent Rewriter — ML"
    assert "version" in body


def test_health_returns_ready(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    # In tests HF and spaCy auto-load are disabled (see conftest.py), so the
    # classifier resolves via the sklearn pickle and the rewriter via the
    # template fallback. We just want each key to be present and boolean.
    assert set(body["models_loaded"].keys()) == {"classifier", "rewriter", "ner"}
    assert all(isinstance(v, bool) for v in body["models_loaded"].values())
    assert body["models_loaded"]["classifier"] is True  # sklearn pickle is committed
    assert body["uptime_seconds"] >= 0
    assert isinstance(body["version"], str)
