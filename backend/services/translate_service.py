"""
translate_service.py - Translation service for LexGuard.

Primary: Google Cloud Translate API
Fallback: MyMemory free translation API
"""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_google_translate_api_key: str = ""
_mymemory_email: str = ""
_cache: dict[str, str] = {}


def init_translate(api_key: str, mymemory_email: str = "") -> None:
    """Configure translation credentials.

    Args:
        api_key: Google Cloud Translate API key.
        mymemory_email: Optional email for MyMemory quota increase.
    """
    global _google_translate_api_key, _mymemory_email
    _google_translate_api_key = api_key
    _mymemory_email = mymemory_email
    logger.info("Translation service initialised.")


def _cache_key(text: str, target_lang: str) -> str:
    """Build a deterministic cache key for a translation request.

    Args:
        text: Source text to translate.
        target_lang: Target language code.

    Returns:
        Cache key string.
    """
    return f"{target_lang}::{hash(text)}"


def _translate_via_google(text: str, target_lang: str) -> Optional[str]:
    """Call Google Cloud Translate REST API.

    Args:
        text: Text to translate.
        target_lang: BCP-47 language code (e.g. 'hi', 'es').

    Returns:
        Translated text string, or None on failure.
    """
    if not _google_translate_api_key:
        return None
    url = "https://translation.googleapis.com/language/translate/v2"
    try:
        resp = requests.post(
            url,
            json={"q": text, "target": target_lang, "format": "text"},
            params={"key": _google_translate_api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["translations"][0]["translatedText"]
    except Exception as exc:
        logger.warning("Google Translate failed: %s", exc)
        return None


def _translate_via_mymemory(text: str, target_lang: str) -> Optional[str]:
    """Fall back to MyMemory free translation API.

    Args:
        text: Text to translate.
        target_lang: Target language code.

    Returns:
        Translated text string, or None on failure.
    """
    url = "https://api.mymemory.translated.net/get"
    params: dict = {"q": text[:500], "langpair": f"en|{target_lang}"}
    if _mymemory_email:
        params["de"] = _mymemory_email
    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        return data["responseData"]["translatedText"]
    except Exception as exc:
        logger.warning("MyMemory fallback failed: %s", exc)
        return None


def translate_text(text: str, target_lang: str) -> dict:
    """Translate text to the target language with automatic fallback.

    Args:
        text: Source text to translate (English assumed).
        target_lang: BCP-47 target language code.

    Returns:
        Dict with keys: 'translated_text', 'source', 'success'.
    """
    if target_lang == "en":
        return {"translated_text": text, "source": "passthrough", "success": True}

    key = _cache_key(text, target_lang)
    if key in _cache:
        return {"translated_text": _cache[key], "source": "cache", "success": True}

    result = _translate_via_google(text, target_lang)
    source = "google"
    if result is None:
        result = _translate_via_mymemory(text, target_lang)
        source = "mymemory"

    if result:
        _cache[key] = result
        return {"translated_text": result, "source": source, "success": True}

    return {"translated_text": text, "source": "fallback", "success": False}
