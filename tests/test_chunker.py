from app.services.chunker import ChunkingService


def test_chunk_returns_multiple_chunks():
    chunker = ChunkingService(chunk_size=50, chunk_overlap=10)
    text = "\n\n".join(f"Sentence number {i} with some padding words." for i in range(10))
    chunks = chunker.chunk(text)
    assert len(chunks) > 1
    assert all(isinstance(c, str) and c.strip() for c in chunks)


def test_chunk_empty_text():
    chunker = ChunkingService()
    assert chunker.chunk("") == []
    assert chunker.chunk("   \n  ") == []


def test_chunk_respects_size():
    chunker = ChunkingService(chunk_size=20, chunk_overlap=0)
    chunks = chunker.chunk("a" * 100)
    # Each chunk must not exceed chunk_size when overlap is 0
    assert all(len(c) <= 20 for c in chunks)
    assert len(chunks) >= 5
