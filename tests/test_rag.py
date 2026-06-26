import pytest

from app.services.rag import RAG_SYSTEM_PROMPT, RAGService
from tests.fakes import FakeEmbedder, FakeVectorStore


def test_system_prompt_grounds_to_context():
    assert "context" in RAG_SYSTEM_PROMPT.lower()
    assert "I don't have enough information" in RAG_SYSTEM_PROMPT


def test_build_prompt_contains_question_and_context():
    rag = RAGService(FakeEmbedder(), FakeVectorStore())
    prompt = rag.build_prompt("What is gradient descent?", ["Gradient descent is an optimizer."])
    assert "What is gradient descent?" in prompt
    assert "Gradient descent is an optimizer." in prompt
    assert "COURSE MATERIALS CONTEXT" in prompt


def test_build_prompt_truncates_large_context(monkeypatch):
    monkeypatch.setenv("MAX_CONTEXT_TOKENS", "10")
    # settings is a singleton; override the attribute directly for the test
    from app.config import settings

    monkeypatch.setattr(settings, "max_context_tokens", 10)
    rag = RAGService(FakeEmbedder(), FakeVectorStore())
    big_chunk = "x" * 10_000
    prompt = rag.build_prompt("q", [big_chunk, big_chunk])
    # Budget = 10 tokens * 4 chars = 40 chars; prompt must be far smaller than 20k chars
    assert prompt.count("x") < 100


@pytest.mark.asyncio
async def test_retrieve_context_returns_texts():
    store = FakeVectorStore()
    store.upsert_chunks("c1", ["alpha chunk", "beta chunk"], [[0.0] * 384, [0.1] * 384], "doc1", "f.txt")
    rag = RAGService(FakeEmbedder(), store)
    chunks = await rag.retrieve_context("query", "c1", top_k=2)
    assert chunks == ["alpha chunk", "beta chunk"]


@pytest.mark.asyncio
async def test_retrieve_context_empty_collection():
    rag = RAGService(FakeEmbedder(), FakeVectorStore())
    assert await rag.retrieve_context("query", "missing", top_k=2) == []
