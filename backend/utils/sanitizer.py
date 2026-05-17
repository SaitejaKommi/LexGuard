"""
sanitizer.py - Input sanitization utilities for LexGuard.

All incoming text and filenames are run through this module before any
processing to prevent injection attacks, XSS, and path traversal.
"""

import re
import unicodedata
from typing import Any

import bleach

from .constants import (
    MAX_CONTRACT_TEXT_LENGTH,
    MAX_CHAT_MESSAGE_LENGTH,
    MAX_FILENAME_LENGTH,
    MAX_SEARCH_QUERY_LENGTH,
)


def sanitize_text(text: str, max_length: int = MAX_CONTRACT_TEXT_LENGTH) -> str:
    """Strip dangerous HTML/JS and enforce length limits on freeform text.

    Args:
        text: Raw input string from the user.
        max_length: Maximum allowed character count.

    Returns:
        Sanitized string, truncated to *max_length* if necessary.

    Raises:
        ValueError: If *text* is not a string or is empty after sanitization.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    cleaned = bleach.clean(text, tags=[], strip=True)
    cleaned = unicodedata.normalize("NFC", cleaned)
    cleaned = cleaned.strip()
    if not cleaned:
        raise ValueError("Input is empty after sanitization.")
    return cleaned[:max_length]


def sanitize_filename(filename: str) -> str:
    """Remove path traversal characters and limit filename length.

    Args:
        filename: Raw filename from the multipart upload.

    Returns:
        Safe filename string.

    Raises:
        ValueError: If filename is blank after sanitization.
    """
    if not isinstance(filename, str):
        raise ValueError("Filename must be a string.")
    # Remove path separators and collapse consecutive dots
    safe = re.sub(r"[/\\]", "_", filename)
    safe = re.sub(r"\.{2,}", "_", safe)
    safe = re.sub(r"[^\w.\-]", "_", safe)
    safe = safe.lstrip(".")
    safe = safe[:MAX_FILENAME_LENGTH]
    if not safe:
        raise ValueError("Filename is empty after sanitization.")
    return safe


def sanitize_chat_message(message: str) -> str:
    """Sanitize a user chat message, enforcing chat-specific length limit.

    Args:
        message: Raw chat input from the user.

    Returns:
        Sanitized chat message string.

    Raises:
        ValueError: If message is empty or too long after cleaning.
    """
    return sanitize_text(message, max_length=MAX_CHAT_MESSAGE_LENGTH)


def sanitize_search_query(query: str) -> str:
    """Sanitize a legal precedent search query.

    Args:
        query: Raw search string from the user.

    Returns:
        Sanitized search query string.

    Raises:
        ValueError: If query is empty after cleaning.
    """
    return sanitize_text(query, max_length=MAX_SEARCH_QUERY_LENGTH)


def sanitize_email(email: str) -> str:
    """Validate and normalise an email address.

    Args:
        email: Raw email string from the user.

    Returns:
        Lower-cased, stripped email address.

    Raises:
        ValueError: If the email format is invalid.
    """
    if not isinstance(email, str):
        raise ValueError("Email must be a string.")
    email = email.strip().lower()
    pattern = r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$"
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email address: {email!r}")
    return email


def sanitize_language_code(code: str) -> str:
    """Ensure a language code is a safe two-to-five character identifier.

    Args:
        code: Raw language/locale code (e.g. 'en', 'hi', 'zh-TW').

    Returns:
        Validated language code in lowercase.

    Raises:
        ValueError: If the code is malformed.
    """
    if not isinstance(code, str):
        raise ValueError("Language code must be a string.")
    code = code.strip().lower()
    if not re.match(r"^[a-z]{2,3}(-[a-z]{2,4})?$", code):
        raise ValueError(f"Invalid language code: {code!r}")
    return code


def sanitize_dict_strings(data: dict[str, Any], max_depth: int = 3) -> dict[str, Any]:
    """Recursively sanitize all string values inside a dictionary.

    Args:
        data: Dictionary whose string values should be sanitized.
        max_depth: Maximum recursion depth to avoid stack overflow.

    Returns:
        New dictionary with all string values sanitized.
    """
    if max_depth <= 0:
        return data
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            try:
                result[key] = sanitize_text(value)
            except ValueError:
                result[key] = ""
        elif isinstance(value, dict):
            result[key] = sanitize_dict_strings(value, max_depth - 1)
        elif isinstance(value, list):
            result[key] = _sanitize_list(value, max_depth - 1)
        else:
            result[key] = value
    return result


def _sanitize_list(items: list[Any], max_depth: int) -> list[Any]:
    """Recursively sanitize string values inside a list.

    Args:
        items: List to sanitize.
        max_depth: Maximum recursion depth.

    Returns:
        Sanitized list.
    """
    result: list[Any] = []
    for item in items:
        if isinstance(item, str):
            try:
                result.append(sanitize_text(item))
            except ValueError:
                result.append("")
        elif isinstance(item, dict):
            result.append(sanitize_dict_strings(item, max_depth))
        elif isinstance(item, list):
            result.append(_sanitize_list(item, max_depth - 1))
        else:
            result.append(item)
    return result
