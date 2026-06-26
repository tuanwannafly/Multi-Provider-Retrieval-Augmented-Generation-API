from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_txt_success():
    resp = client.post(
        "/documents/upload",
        data={"collection": "math-101"},
        files={"file": ("note.txt", b"Gradient descent minimizes a function.", "text/plain")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["doc_id"].startswith("sha256:")
    assert data["collection"] == "math-101"
    assert data["chunks_created"] >= 0
    assert data["deduplicated"] is False


def test_upload_unsupported_type():
    resp = client.post(
        "/documents/upload",
        data={"collection": "demo"},
        files={"file": ("slides.pptx", b"binary stuff", "application/vnd.ms-powerpoint")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_invalid_collection_name():
    resp = client.post(
        "/documents/upload",
        data={"collection": "Math 101"},
        files={"file": ("note.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "INVALID_COLLECTION_NAME"
