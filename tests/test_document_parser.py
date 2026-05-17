"""test_document_parser.py - Tests for document parsing pipeline."""
import pytest
from backend.services.document_parser import parse_document, _validate_magic_bytes


def test_parse_txt_bytes():
    data = b"This is a plain text contract."
    result = parse_document(data, "contract.txt")
    assert result["file_type"] == "txt"
    assert "plain text" in result["text"]
    assert result["char_count"] > 0


def test_parse_txt_too_large():
    data = b"x" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="size"):
        parse_document(data, "big.txt")


def test_parse_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported"):
        parse_document(b"data", "file.exe")


def test_validate_magic_bytes_pdf_wrong():
    with pytest.raises(ValueError, match="magic"):
        _validate_magic_bytes(b"notapdf", "pdf")


def test_validate_magic_bytes_docx_wrong():
    with pytest.raises(ValueError, match="magic"):
        _validate_magic_bytes(b"notadocx", "docx")


def test_validate_magic_bytes_pdf_ok():
    _validate_magic_bytes(b"%PDF-1.4 content", "pdf")  # should not raise


def test_validate_magic_bytes_txt_skipped():
    _validate_magic_bytes(b"anything", "txt")  # no magic for txt


def test_parse_txt_latin1():
    data = "Caf\xe9 contract".encode("latin-1")
    result = parse_document(data, "cafe.txt")
    assert result["char_count"] > 0
