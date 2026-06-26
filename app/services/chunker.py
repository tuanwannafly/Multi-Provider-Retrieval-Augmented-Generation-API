"""Text chunking service wrapping LangChain's RecursiveCharacterTextSplitter."""
from __future__ import annotations

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


class ChunkingService:
    def __init__(
        self,
        chunk_size: int = settings.default_chunk_size,
        chunk_overlap: int = settings.default_chunk_overlap,
        separators: List[str] | None = None,
    ):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators or ["\n\n", "\n", " "],
            length_function=len,
        )

    def chunk(self, text: str) -> List[str]:
        """Split text into non-empty chunks."""
        if not text or not text.strip():
            return []
        return [c for c in self._splitter.split_text(text) if c.strip()]
