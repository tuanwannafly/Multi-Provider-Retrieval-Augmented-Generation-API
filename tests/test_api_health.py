from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_readiness_shape():
    resp = client.get("/readiness")
    assert resp.status_code == 200
    data = resp.json()
    for key in ("status", "embedding_model", "qdrant", "qdrant_url"):
        assert key in data
