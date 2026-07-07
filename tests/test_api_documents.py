from fastapi.testclient import TestClient

from app.deps import get_embedder, get_vector_store
from app.main import app
from tests.fakes import FakeEmbedder, FakeVectorStore

client = TestClient(app)

_shared_store = FakeVectorStore()


def _override_deps():
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_vector_store] = lambda: _shared_store


def _reset_deps():
    app.dependency_overrides.clear()


def test_upload_txt_success():
    _override_deps()
    try:
        resp = client.post(
            "/api/documents/upload",
            data={"collection": "math-101"},
            files={
                "file": (
                    "note.txt",
                    b"Gradient descent minimizes a function by moving "
                    b"in the direction of steepest descent. The learning "
                    b"rate controls the step size during optimization.",
                    "text/plain",
                )
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["doc_id"].startswith("sha256:")
        assert data["collection"] == "math-101"
        assert data["chunks_created"] >= 1
        assert data["deduplicated"] is False
    finally:
        _reset_deps()


def test_upload_dedup_returns_409():
    _shared_store2 = FakeVectorStore()
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_vector_store] = lambda: _shared_store2
    try:
        payload = {
            "data": {"collection": "dup"},
            "files": {
                "file": (
                    "note.txt",
                    b"Duplicate content for dedup detection test. " * 20,
                    "text/plain",
                )
            },
        }
        first = client.post("/api/documents/upload", **payload)
        assert first.status_code == 200
        second = client.post("/api/documents/upload", **payload)
        assert second.status_code == 409
        assert second.json()["error"] == "DUPLICATE_DOCUMENT"
    finally:
        _reset_deps()


def test_upload_unsupported_type():
    resp = client.post(
        "/api/documents/upload",
        data={"collection": "demo"},
        files={"file": ("slides.pptx", b"binary stuff", "application/vnd.ms-powerpoint")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_invalid_collection_name():
    resp = client.post(
        "/api/documents/upload",
        data={"collection": "Math 101"},
        files={"file": ("note.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "INVALID_COLLECTION_NAME"
