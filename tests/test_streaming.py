import pytest
from fastapi.testclient import TestClient

from app.deps import get_embedder, get_rag_service, get_vector_store
from app.main import app
from app.services.llm import factory
from app.services.llm.base import LLMResponse
from app.services.rag import RAGService
from tests.fakes import FakeEmbedder, FakeVectorStore

client = TestClient(app)


class StreamingFakeProvider:
    """Provider that streams tokens word-by-word."""

    def __init__(self, name="groq"):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def model_id(self):
        return "fake-stream"

    async def complete(self, prompt, system=""):
        return LLMResponse(answer="full answer", model="fake-stream", latency_ms=10, tokens=5)

    async def complete_stream(self, prompt, system=""):
        for word in ["Hello ", "streaming ", "world"]:
            yield word


def _setup():
    store = FakeVectorStore()
    store.upsert_chunks(
        "ml-basics",
        ["Supervised learning uses labeled data."],
        [[0.0] * 384],
        "sha256:s1",
        "f.txt",
    )
    factory.reset_registry()
    factory.set_provider("groq", StreamingFakeProvider())
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_vector_store] = lambda: store
    app.dependency_overrides[get_rag_service] = lambda: RAGService(FakeEmbedder(), store)


def _teardown():
    app.dependency_overrides.clear()
    factory.reset_registry()


def test_ask_stream_returns_sse():
    _setup()
    try:
        with client.stream(
            "POST",
            "/api/ask",
            json={
                "question": "What is supervised learning?",
                "collection": "ml-basics",
                "provider": "groq",
                "stream": True,
            },
        ) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]
            body = "".join(resp.iter_lines())
            assert "data:" in body
            assert "Hello " in body
            assert "streaming " in body
            assert '"done": true' in body
    finally:
        _teardown()


def test_ask_non_stream_still_json():
    _setup()
    try:
        resp = client.post(
            "/api/ask",
            json={
                "question": "What is supervised learning?",
                "collection": "ml-basics",
                "provider": "groq",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"
        assert "answer" in resp.json()
    finally:
        _teardown()
