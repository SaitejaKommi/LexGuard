"""test_sanitizer.py - Tests for input sanitization utilities."""
import pytest
from backend.utils.sanitizer import (
    sanitize_text, sanitize_filename, sanitize_chat_message,
    sanitize_email, sanitize_language_code
)


def test_sanitize_text_strips_html():
    result = sanitize_text("<script>alert('xss')</script>Hello")
    assert "<script>" not in result
    assert "Hello" in result


def test_sanitize_text_rejects_non_string():
    with pytest.raises(ValueError):
        sanitize_text(12345)


def test_sanitize_text_enforces_max_length():
    long = "a" * 100000
    result = sanitize_text(long, max_length=100)
    assert len(result) <= 100


def test_sanitize_text_raises_on_empty():
    with pytest.raises(ValueError):
        sanitize_text("   ")


def test_sanitize_filename_removes_path_traversal():
    result = sanitize_filename("../../etc/passwd")
    assert ".." not in result
    assert "/" not in result


def test_sanitize_filename_allows_normal():
    result = sanitize_filename("contract.pdf")
    assert result == "contract.pdf"


def test_sanitize_email_valid():
    result = sanitize_email("User@Example.COM")
    assert result == "user@example.com"


def test_sanitize_email_invalid():
    with pytest.raises(ValueError):
        sanitize_email("not-an-email")


def test_sanitize_language_code_valid():
    assert sanitize_language_code("en") == "en"
    assert sanitize_language_code("zh-TW") == "zh-tw"


def test_sanitize_language_code_invalid():
    with pytest.raises(ValueError):
        sanitize_language_code("123!!!")
