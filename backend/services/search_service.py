"""
search_service.py - Legal precedent search service for LexGuard.

Primary: Google Custom Search API
Fallback: Static curated legal precedent results
"""

import logging
from typing import Optional

import requests

from ..utils.constants import SEARCH_CACHE_TTL, SEARCH_FALLBACK_RESULTS

logger = logging.getLogger(__name__)

_google_api_key: str = ""
_search_engine_id: str = ""
_cache: dict[str, list] = {}
_cache_timestamps: dict[str, float] = {}


def init_search(api_key: str, engine_id: str) -> None:
    """Configure Google Custom Search credentials.

    Args:
        api_key: Google Custom Search API key.
        engine_id: Programmable Search Engine ID (cx parameter).
    """
    global _google_api_key, _search_engine_id
    _google_api_key = api_key
    _search_engine_id = engine_id
    logger.info("Search service initialised.")


def _is_cache_valid(query: str) -> bool:
    """Check whether a cached result is still within the TTL window.

    Args:
        query: Search query string used as cache key.

    Returns:
        True if cache entry is fresh, False otherwise.
    """
    import time

    ts = _cache_timestamps.get(query, 0)
    return (time.time() - ts) < SEARCH_CACHE_TTL


def _search_via_google(query: str, num_results: int = 6) -> Optional[list]:
    """Call Google Custom Search API.

    Args:
        query: Legal precedent search query.
        num_results: Maximum number of results to retrieve.

    Returns:
        List of result dicts, or None on failure.
    """
    if not _google_api_key or not _search_engine_id:
        return None

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": _google_api_key,
        "cx": _search_engine_id,
        "q": f"legal precedent contract law {query}",
        "num": num_results,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
            }
            for item in items
        ]
    except Exception as exc:
        logger.warning("Google Custom Search failed: %s", exc)
        return None


def search_legal_precedents(query: str) -> dict:
    """Search for legal precedents and standards related to the query.

    Args:
        query: Legal search query string.

    Returns:
        Dict with keys: 'results' (list), 'source' ('google' or 'fallback'), 'success' (bool).
    """
    import time

    if query in _cache and _is_cache_valid(query):
        return {"results": _cache[query], "source": "cache", "success": True}

    results = _search_via_google(query)
    source = "google"

    if not results:
        results = SEARCH_FALLBACK_RESULTS
        source = "fallback"

    _cache[query] = results
    _cache_timestamps[query] = time.time()

    return {"results": results, "source": source, "success": True}
