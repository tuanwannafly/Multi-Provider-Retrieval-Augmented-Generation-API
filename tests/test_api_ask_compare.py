from fastapi.testclient import TestClient

from app.deps import get_embedder, get_rag_service, get_vector_store
from app.main import app
from app.services.llm import factory
from app.services.llm.base import LLMResponse
from tests.fakes import FakeEmbedder, FakeVectorStore

client = TestClient(app)

_shared_store = FakeVectorStore()


class FakeProvider:
    def __init__(self, name, model="fake-model", answer="A grounded answer.", latency=10, tokens=42, fail=False):
        self._name = name
        self._model = model
        self._answer = answer
        self._latency = latency
        self._tokens = tokens
        self._fail = fail

    @property
    def name(self):
        return self._name

    @property
    def model_id(self):
        return self._model

    async def complete(self, prompt, system=""):
        if self._fail:
            from app.services.llm.base import ProviderUnavailableError

            raise ProviderUnavailableError(f"{self._name} boom")
        return LLMResponse(
            answer=self._answer, model=self._model, latency_ms=self._latency, tokens=self._tokens
        )


def _seed_and_override(providers=None):
    factory.reset_registry()
    _shared_store.delete_collection("ml-basics")
    _shared_store.upsert_chunks(
        "ml-basics",
        [
            "Supervised learning uses labeled data to train models.",
            "Unsupervised learning finds structure in unlabeled data.",
        ],
        [[0.0] * 384, [0.1] * 384],
        "sha256:seed",
        "intro.txt",
    )
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_vector_store] = lambda: _shared_store
    app.dependency_overrides[get_rag_service] = lambda: None  # bypass real RAGService init
    from app.services.rag import RAGService

    app.dependency_overrides[get_rag_service] = lambda: RAGService(FakeEmbedder(), _shared_store)

    factory.set_provider("groq", providers.get("groq", FakeProvider("groq")))
    factory.set_provider("gemini", providers.get("gemini", FakeProvider("gemini")))
    factory.set_provider("anthropic", providers.get("anthropic", FakeProvider("anthropic")))


def _reset():
    app.dependency_overrides.clear()
    factory.reset_registry()


def test_ask_success():
    _seed_and_override()
    try:
        resp = client.post(
            "/api/ask",
            json={"question": "What is supervised learning?", "collection": "ml-basics", "provider": "groq"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["provider"] == "groq"
        assert len(data["answer"]) > 0
        assert data["chunks_used"] >= 1
        assert data["collection"] == "ml-basics"
    finally:
        _reset()


def test_ask_collection_not_found():
    _seed_and_override()
    try:
        resp = client.post(
            "/api/ask",
            json={"question": "anything", "collection": "missing", "provider": "groq"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"] == "COLLECTION_NOT_FOUND"
    finally:
        _reset()


def test_ask_invalid_provider():
    _seed_and_override()
    try:
        resp = client.post(
            "/api/ask",
            json={"question": "anything", "collection": "ml-basics", "provider": "openai"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "INVALID_PROVIDER"
    finally:
        _reset()


def test_compare_all_success_and_fastest():
    providers = {
        "groq": FakeProvider("groq", latency=100),
        "gemini": FakeProvider("gemini", latency=50),
        "anthropic": FakeProvider("anthropic", latency=300),
    }
    _seed_and_override(providers)
    try:
        resp = client.post(
            "/api/compare",
            json={"question": "supervised vs unsupervised", "collection": "ml-basics"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert set(data["results"].keys()) == {"groq", "gemini", "anthropic"}
        assert all(r["status"] == "success" for r in data["results"].values())
        assert data["fastest_provider"] == "gemini"
    finally:
        _reset()


def test_compare_graceful_degradation():
    providers = {
        "groq": FakeProvider("groq", latency=100),
        "gemini": FakeProvider("gemini", fail=True),
        "anthropic": FakeProvider("anthropic", latency=300),
    }
    _seed_and_override(providers)
    try:
        resp = client.post(
            "/api/compare",
            json={"question": "supervised vs unsupervised", "collection": "ml-basics"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"]["gemini"]["status"] == "error"
        assert data["results"]["groq"]["status"] == "success"
        # fastest must skip the failed provider
        assert data["fastest_provider"] in ("groq", "anthropic")
    finally:
        _reset()
