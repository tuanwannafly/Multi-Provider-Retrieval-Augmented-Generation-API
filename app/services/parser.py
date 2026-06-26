"""File parsing service: PDF/DOCX/TXT -> plain text + deterministic doc_id."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Optional


class UnsupportedFileTypeError(ValueError):
    """Raised when an uploaded file type is not supported."""


class FileParser:
    SUPPORTED_TYPES = {".pdf", ".docx", ".txt"}

    def parse(self, file_bytes: bytes, filename: str) -> dict:
        suffix = Path(filename).suffix.lower()
        if suffix not in self.SUPPORTED_TYPES:
            raise UnsupportedFileTypeError(
                f"File type '{suffix}' is not supported. "
                f"Allowed: {', '.join(sorted(self.SUPPORTED_TYPES))}"
            )

        doc_id = "sha256:" + hashlib.sha256(file_bytes).hexdigest()[:16]
        page_count: Optional[int] = None

        if suffix == ".pdf":
            text = self._parse_pdf(file_bytes)
        elif suffix == ".docx":
            text = self._parse_docx(file_bytes)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")

        return {"doc_id": doc_id, "text": text, "source": filename}

    def _parse_pdf(self, data: bytes) -> str:
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages).strip()

    def _parse_docx(self, data: bytes) -> str:
        import docx

        document = docx.Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in document.paragraphs if p.text.strip())
