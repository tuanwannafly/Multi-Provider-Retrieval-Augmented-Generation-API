"""End-to-end integration tests using fakes (no external Qdrant / LLM APIs).

Mirrors the production flow: upload -> ask -> evaluate, plus /compare.
Run the real-service variant with: pytest -m integration (requires live services).
"""
from __future__ import annotations

import io

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
        "/documents/upload",
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
        "/ask",
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
        "/evaluate",
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
        "/documents/upload",
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
        "/compare",
        json={"question": "supervised vs unsupervised", "collection": _E2E_COLLECTION},
    )
    assert compare.status_code == 200, compare.text
    data = compare.json()
    assert set(data["results"]) == {"groq", "gemini", "anthropic"}
    assert all(r["status"] == "success" for r in data["results"].values())
    assert data["fastest_provider"] in ("groq", "gemini", "anthropic")
    assert data["context_chunks"] >= 1


def test_upload_then_list_then_delete(e2e_env):
    client.post(
        "/documents/upload",
        data={"collection": "lifecycle"},
        files={"file": ("note.txt", b"Document lifecycle integration test content.", "text/plain")},
    )

    listed = client.get("/collections").json()
    names = [c["name"] for c in listed["collections"]]
    assert "lifecycle" in names

    deleted = client.delete("/collections/lifecycle")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    again = client.delete("/collections/lifecycle")
    assert again.status_code == 404
