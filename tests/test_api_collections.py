from fastapi.testclient import TestClient

from app.deps import get_embedder, get_vector_store
from app.main import app
from tests.fakes import FakeEmbedder, FakeVectorStore

client = TestClient(app)

_shared_store = FakeVectorStore()


def setup_module(module):
    app.dependency_overrides[get_vector_store] = lambda: _shared_store
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    # Seed one collection via the upload endpoint
    client.post(
        "/documents/upload",
        data={"collection": "ml-basics"},
        files={
            "file": (
                "intro.txt",
                b"Machine learning lets systems learn patterns from data. "
                b"Supervised learning uses labeled examples while unsupervised "
                b"learning finds structure without labels.",
                "text/plain",
            )
        },
    )


def teardown_module(module):
    app.dependency_overrides.clear()


def test_list_collections():
    resp = client.get("/collections")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_collections"] >= 1
    assert any(c["name"] == "ml-basics" for c in data["collections"])
    assert data["total_chunks"] >= 1


def test_delete_collection():
    resp = client.delete("/collections/ml-basics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted"] is True
    assert data["name"] == "ml-basics"
    assert data["points_removed"] >= 1

    # Second delete -> 404
    again = client.delete("/collections/ml-basics")
    assert again.status_code == 404
    assert again.json()["error"] == "COLLECTION_NOT_FOUND"
