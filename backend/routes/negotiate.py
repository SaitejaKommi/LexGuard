"""
negotiate.py - /api/negotiate route for contract negotiation recommendations in LexGuard.

Accepts high-risk clauses and returns AI-powered negotiation guidance.
"""

import logging

from flask import Blueprint, request, jsonify

from ..services import gemini_service
from ..utils.constants import ERROR_CODES

logger = logging.getLogger(__name__)
negotiate_bp = Blueprint("negotiate", __name__, url_prefix="/api")


@negotiate_bp.route("/negotiate", methods=["POST"])
def negotiate():
    """Generate negotiation recommendations for high-risk clauses.

    Expects JSON body:
        - clauses (list): Array of clause objects with risk_level field

    Returns:
        JSON with 'recommendations' array of negotiation guidance objects.
    """
    body = request.get_json(silent=True) or {}
    clauses = body.get("clauses", [])

    if not clauses or not isinstance(clauses, list):
        return jsonify({
            "error": "Field 'clauses' is required and must be a non-empty array.",
            "code": "MISSING_FIELD",
        }), 400

    # Filter to only high/critical risk clauses if not already filtered
    risky_clauses = [
        c for c in clauses
        if isinstance(c, dict) and c.get("risk_level") in ("HIGH", "CRITICAL", "MEDIUM")
    ]

    if not risky_clauses:
        return jsonify({
            "recommendations": [],
            "message": "No high-risk clauses found requiring negotiation.",
        }), 200

    try:
        recommendations = gemini_service.generate_negotiation_recommendations(risky_clauses)
    except RuntimeError as exc:
        logger.error("Negotiation generation failed: %s", exc)
        return jsonify({"error": str(exc), "code": "GEMINI_ERROR"}), 502

    return jsonify({
        "recommendations": recommendations,
        "count": len(recommendations),
    }), 200
