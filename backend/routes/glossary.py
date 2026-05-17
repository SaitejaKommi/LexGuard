"""
glossary.py - /api/glossary route for legal term definitions in LexGuard.

Accepts a legal term and returns a plain-English definition via Gemini.
"""

import logging

from flask import Blueprint, request, jsonify

from ..services import gemini_service
from ..utils.sanitizer import sanitize_text
from ..utils.constants import ERROR_CODES

logger = logging.getLogger(__name__)
glossary_bp = Blueprint("glossary", __name__, url_prefix="/api")


@glossary_bp.route("/glossary", methods=["POST"])
def glossary():
    """Explain a legal term in plain English.

    Expects JSON body:
        - term (str): Legal term to define (max 200 chars)

    Returns:
        JSON with term, definition, example, related_terms, risk_note.
    """
    body = request.get_json(silent=True) or {}
    raw_term = body.get("term", "")

    if not raw_term:
        return jsonify({
            "error": "Field 'term' is required.",
            "code": "MISSING_FIELD",
        }), 400

    try:
        term = sanitize_text(str(raw_term), max_length=200)
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_INPUT"}), 400

    try:
        result = gemini_service.explain_legal_term(term)
    except RuntimeError as exc:
        logger.error("Glossary lookup failed: %s", exc)
        return jsonify({"error": str(exc), "code": "GEMINI_ERROR"}), 502

    return jsonify(result), 200
