"""
search.py - /api/search route for legal precedent search in LexGuard.

Delegates to Google Custom Search with a static curated fallback.
"""

import logging

from flask import Blueprint, request, jsonify

from ..services import search_service
from ..utils.sanitizer import sanitize_search_query
from ..utils.constants import ERROR_CODES

logger = logging.getLogger(__name__)
search_bp = Blueprint("search", __name__, url_prefix="/api")


@search_bp.route("/search", methods=["GET"])
def search():
    """Search for legal precedents and standards related to a query.

    Query Parameters:
        q (str): Search query string (max 500 chars)

    Returns:
        JSON with 'results' list and 'source' ('google' or 'fallback').
    """
    raw_query = request.args.get("q", "")
    if not raw_query:
        return jsonify({"error": "Query parameter 'q' is required.", "code": "MISSING_FIELD"}), 400

    try:
        query = sanitize_search_query(raw_query)
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_INPUT"}), 400

    result = search_service.search_legal_precedents(query)
    return jsonify(result), 200
