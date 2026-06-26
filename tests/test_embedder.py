import pytest

from app.services.embedder import EmbeddingService, ModelNotLoadedError


def test_singleton_instance():
    a = EmbeddingService.get_instance()
    b = EmbeddingService.get_instance()
    assert a is b
    assert a.is_loaded() is False


@pytest.mark.asyncio
async def test_embed_before_load_raises():
    embedder = EmbeddingService.get_instance()
    if not embedder.is_loaded():
        with pytest.raises(ModelNotLoadedError):
            await embedder.embed_texts(["hello"])


@pytest.mark.asyncio
async def test_embed_deterministic():
    """Requires the real sentence-transformers model; skipped if unavailable."""
    pytest.importorskip("sentence_transformers")
    embedder = EmbeddingService.get_instance()
    if not embedder.is_loaded():
        embedder.load_model()
    v1 = await embedder.embed_query("gradient descent")
    v2 = await embedder.embed_query("gradient descent")
    assert v1 == v2
    assert len(v1) == 384
