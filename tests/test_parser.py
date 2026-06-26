import io

import pytest

from app.services.parser import FileParser, UnsupportedFileTypeError


def _make_docx(text: str) -> bytes:
    import docx

    document = docx.Document()
    for paragraph in text.split("\n\n"):
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _make_pdf(text: str) -> bytes:
    reportlab = pytest.importorskip("reportlab")
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    for i, line in enumerate(text.split("\n")):
        c.drawString(72, 800 - 20 * i, line)
    c.showPage()
    c.save()
    return buffer.getvalue()


def test_parse_txt():
    parser = FileParser()
    result = parser.parse(b"Hello RAG world", "note.txt")
    assert result["text"] == "Hello RAG world"
    assert result["doc_id"].startswith("sha256:")
    assert len(result["doc_id"]) == len("sha256:") + 16


def test_parse_docx():
    parser = FileParser()
    data = _make_docx("First paragraph.\n\nSecond paragraph.")
    result = parser.parse(data, "doc.docx")
    assert "First paragraph" in result["text"]
    assert "Second paragraph" in result["text"]


def test_parse_pdf():
    parser = FileParser()
    data = _make_pdf("Gradient descent minimizes a function.")
    result = parser.parse(data, "lecture.pdf")
    assert "Gradient descent" in result["text"]


def test_parse_unsupported_type():
    parser = FileParser()
    with pytest.raises(UnsupportedFileTypeError):
        parser.parse(b"data", "slides.pptx")


def test_doc_id_is_deterministic():
    parser = FileParser()
    payload = b"identical content for dedup check"
    a = parser.parse(payload, "a.txt")
    b = parser.parse(payload, "b.txt")
    assert a["doc_id"] == b["doc_id"]


def test_different_content_different_doc_id():
    parser = FileParser()
    assert parser.parse(b"content one", "a.txt")["doc_id"] != parser.parse(
        b"content two", "a.txt"
    )["doc_id"]
