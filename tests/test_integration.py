"""End-to-end integration tests using fakes (no external Qdrant / LLM APIs).

Mirrors the production flow: upload -> ask -> evaluate, plus /compare.
Run the real-service variant with: pytest -m integration (requires live services).
"""
from __future__ import annotations

import io
import os
import pytest
from fastapi.testclient import TestClient

from app.deps import (
    get_embedder,
    get_evaluator,
    get_parser,
    get_rag_service,
    get_vector_store,
)
from app.main import app
from app.services.evaluator import RAGEvaluator
from app.services.llm import factory
from app.services.llm.base import LLMResponse
from app.services.rag import RAGService
from app.services.vector_store import QdrantService # Import QdrantService
from tests.fakes import FakeEmbedder, FakeVectorStore

client = TestClient(app)

_E2E_COLLECTION = "test-integration"


@pytest.fixture()
def e2e_env():
    store = FakeVectorStore()
    factory.reset_registry()

    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_vector_store] = lambda: store
    app.dependency_overrides[get_rag_service] = lambda: RAGService(FakeEmbedder(), store)
    app.dependency_overrides[get_evaluator] = lambda: RAGEvaluator(FakeEmbedder())

    class StubProvider:
        def __init__(self, name, answer, latency=12, tokens=99):
            self._name = name
            self._answer = answer
            self._latency = latency
            self._tokens = tokens

        @property
        def name(self):
            return self._name

        @property
        def model_id(self):
            return f"{self._name}-stub"

        async def complete(self, prompt, system=""):
            return LLMResponse(
                answer=self._answer,
                model=self.model_id,
                latency_ms=self._latency,
                tokens=self._tokens,
            )

    factory.set_provider("groq", StubProvider("groq", "Supervised learning uses labeled data."))
    factory.set_provider("gemini", StubProvider("gemini", "Labeled examples guide the model.", latency=30))
    factory.set_provider("anthropic", StubProvider("anthropic", "It trains on input-output pairs.", latency=40))

    yield store
    app.dependency_overrides.clear()
    factory.reset_registry()


def test_full_rag_flow(e2e_env):
    # 1. Upload a text document (parse -> chunk -> embed -> store)
    upload = client.post(
        "/api/documents/upload", # Updated path
        data={"collection": _E2E_COLLECTION},
        files={
            "file": (
                "intro.txt",
                b"Supervised learning uses labeled training data to teach a model. "
                b"Each example pairs inputs with a target output. The model learns a "
                b"mapping from inputs to outputs. Gradient descent optimizes the weights.",
                "text/plain",
            )
        },
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["chunks_created"] > 0

    # 2. Ask a question
    ask = client.post(
        "/api/ask", # Updated path
        json={
            "question": "What is supervised learning?",
            "collection": _E2E_COLLECTION,
            "provider": "groq",
        },
    )
    assert ask.status_code == 200, ask.text
    ask_data = ask.json()
    assert len(ask_data["answer"]) > 0
    assert ask_data["chunks_used"] >= 1

    # 3. Evaluate the answer
    evaluate = client.post(
        "/api/evaluate", # Updated path
        json={
            "question": "What is supervised learning?",
            "answer": ask_data["answer"],
            "context": ask_data["context_preview"],
            "ground_truth": "Supervised learning uses labeled training data.",
        },
    )
    assert evaluate.status_code == 200, evaluate.text
    eval_data = evaluate.json()
    assert 0.0 <= eval_data["faithfulness"] <= 1.0
    assert 0.0 <= eval_data["answer_relevancy"] <= 1.0


def test_compare_endpoint(e2e_env):
    # Seed collection first
    client.post(
        "/api/documents/upload", # Updated path
        data={"collection": _E2E_COLLECTION},
        files={
            "file": (
                "intro.txt",
                b"Supervised learning uses labeled training data. "
                b"Unsupervised learning finds structure without labels.",
                "text/plain",
            )
        },
    )

    compare = client.post(
        "/api/compare", # Updated path
        json={"question": "supervised vs unsupervised", "collection": _E2E_COLLECTION},
    )
    assert compare.status_code == 200, compare.text
    data = compare.json()
    assert set(data["results"].keys()) == {"groq", "gemini", "anthropic"}
    assert all(r["status"] == "success" for r in data["results"].values())
    assert data["fastest_provider"] in ("groq", "gemini", "anthropic")
    assert data["context_chunks"] >= 1


def test_upload_then_list_then_delete(e2e_env):
    client.post(
        "/api/documents/upload", # Updated path
        data={"collection": "lifecycle"},
        files={"file": ("note.txt", b"Document lifecycle integration test content.", "text/plain")},
    )

    listed = client.get("/api/collections").json() # Updated path
    names = [c["name"] for c in listed["collections"]]
    assert "lifecycle" in names

    deleted = client.delete("/api/collections/lifecycle") # Updated path
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    again = client.delete("/api/collections/lifecycle") # Updated path
    assert again.status_code == 404


@pytest.fixture()
def real_qdrant_env(monkeypatch):
    # Ensure Qdrant URL is set for real client
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr("app.config.settings.qdrant_url", qdrant_url)
    monkeypatch.setattr("app.config.settings.qdrant_collection_dim", 384)
    monkeypatch.setattr("app.config.settings.embedding_model", "sentence-transformers/all-MiniLM-L6-v2")

    # Override dependencies to use real services
    app.dependency_overrides[get_vector_store] = lambda: QdrantService(url=qdrant_url, vector_size=384)
    # Ensure embedder is loaded in main.py lifespan, or manually load for this test
    # For CI, RAG_PRELOAD_EMBEDDING is "0", so we need to ensure it's loaded
    embedder = get_embedder()
    if not embedder.is_loaded():
        embedder.load_model()
    app.dependency_overrides[get_embedder] = lambda: embedder
    app.dependency_overrides[get_rag_service] = lambda: RAGService(embedder=embedder, vector_store=QdrantService(url=qdrant_url, vector_size=384))

    # Clear any existing collections for a clean test run
    qdrant_client = QdrantService(url=qdrant_url)
    for collection in qdrant_client.list_collections():
        qdrant_client.delete_collection(collection["name"])

    yield qdrant_client # Yield the real QdrantService instance

    # Clean up after test
    for collection in qdrant_client.list_collections():
        qdrant_client.delete_collection(collection["name"])
    app.dependency_overrides.clear()
    factory.reset_registry()


@pytest.mark.integration # Mark this test for integration suite
def test_real_qdrant_integration(real_qdrant_env):
    # 1. Upload a document to real Qdrant
    upload_resp = client.post(
        "/api/documents/upload", # Updated path
        data={"collection": "real-integration-test"},
        files={
            "file": (
                "real_doc.txt",
                b"This is a document for real Qdrant integration testing. It contains important information.",
                "text/plain",
            )
        },
    )
    assert upload_resp.status_code == 200, upload_resp.text
    assert upload_resp.json()["chunks_created"] > 0

    # 2. Check readiness endpoint (should be ready after Qdrant probe in lifespan)
    readiness_resp = client.get("/readiness") # Root path
    assert readiness_resp.status_code == 200, readiness_resp.text
    assert readiness_resp.json()["status"] == "ready"
    assert readiness_resp.json()["qdrant"] == "connected"
    assert readiness_resp.json()["embedding_model"] == "loaded"


    # 3. Ask a question and retrieve context from real Qdrant
    ask_resp = client.post(
        "/api/ask", # Updated path
        json={
            "question": "What is this document about?",
            "collection": "real-integration-test",
            "provider": "groq", # Using a stubbed LLM for now, focus on Qdrant
        },
    )
    assert ask_resp.status_code == 200, ask_resp.text
    ask_data = ask_resp.json()
    assert len(ask_data["answer"]) > 0
    assert ask_data["chunks_used"] >= 1
    assert "real-integration-test" in ask_data["collection"]
