from fastapi.testclient import TestClient

from app.deps import get_embedder, get_vector_store
from app.main import app
from tests.fakes import FakeEmbedder, FakeVectorStore

client = TestClient(app)


def test_x_process_time_header():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "X-Process-Time-Ms" in resp.headers


def test_error_envelope_format():
    resp = client.post(
        "/api/documents/upload",
        data={"collection": "Bad Name!"},
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    body = resp.json()
    for key in ("error", "message", "status_code", "request_id"):
        assert key in body
    assert body["request_id"].startswith("req_")


def test_internal_error_envelope(monkeypatch):
    # Force an unhandled exception inside the documents router path by making the
    # parser raise something that is NOT a domain exception.
    from app.deps import get_parser
    from app.services.parser import FileParser

    class BoomParser(FileParser):
        def parse(self, file_bytes, filename):
            raise RuntimeError("boom")

    app.dependency_overrides[get_parser] = lambda: BoomParser()
    try:
        resp = client.post(
            "/api/documents/upload",
            data={"collection": "demo"},
            files={"file": ("note.txt", b"hello world", "text/plain")},
        )
        assert resp.status_code == 500
        body = resp.json()
        assert body["error"] == "INTERNAL_ERROR"
        assert body["status_code"] == 500
        assert "request_id" in body
    finally:
        app.dependency_overrides.clear()
