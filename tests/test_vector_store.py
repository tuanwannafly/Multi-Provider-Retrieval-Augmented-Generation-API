from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.vector_store import QdrantService


def _make_service_with_mock():
    service = QdrantService.__new__(QdrantService)
    service.client = MagicMock()
    service.vector_size = 384
    return service


def test_ensure_collection_creates_when_missing():
    service = _make_service_with_mock()
    service.client.get_collections.return_value = SimpleNamespace(collections=[])
    service.ensure_collection("math-101")
    service.client.create_collection.assert_called_once()
    args, kwargs = service.client.create_collection.call_args
    assert kwargs["collection_name"] == "math-101"


def test_ensure_collection_skips_when_exists():
    service = _make_service_with_mock()
    service.client.get_collections.return_value = SimpleNamespace(
        collections=[SimpleNamespace(name="math-101")]
    )
    service.ensure_collection("math-101")
    service.client.create_collection.assert_not_called()


def test_upsert_chunks_uses_deterministic_ids():
    service = _make_service_with_mock()
    chunks = ["alpha", "beta"]
    embeddings = [[0.1] * 384, [0.2] * 384]
    created = service.upsert_chunks("c1", chunks, embeddings, "sha256:abc", "f.txt")
    assert created == 2
    service.client.upsert.assert_called_once()
    _, kwargs = service.client.upsert.call_args
    points = kwargs["points"]
    assert points[0].id != points[1].id
    assert points[0].payload["doc_id"] == "sha256:abc"
    assert points[0].payload["chunk_index"] == 0


def test_check_duplicate_true():
    service = _make_service_with_mock()
    service.client.get_collections.return_value = SimpleNamespace(
        collections=[SimpleNamespace(name="c1")]
    )
    service.client.scroll.return_value = ([object()], None)
    assert service.check_duplicate("c1", "sha256:abc") is True


def test_check_duplicate_false_when_collection_missing():
    service = _make_service_with_mock()
    service.client.get_collections.return_value = SimpleNamespace(collections=[])
    assert service.check_duplicate("missing", "sha256:abc") is False
    service.client.scroll.assert_not_called()
