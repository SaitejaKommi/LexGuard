"""
history.py - /api/history routes for analysis history retrieval in LexGuard.
"""

import logging

from flask import Blueprint, request, jsonify, session

from ..services import mongodb_service
from ..utils.sanitizer import sanitize_email

logger = logging.getLogger(__name__)
history_bp = Blueprint("history", __name__, url_prefix="/api")


@history_bp.route("/history", methods=["GET"])
def get_history():
    """Return the analysis history for a user.

    Query Parameters:
        email (str): User email address

    Returns:
        JSON with 'history' list of past analyses.
    """
    raw_email = request.args.get("email", "")
    if not raw_email:
        return jsonify({"error": "Email parameter required.", "code": "MISSING_FIELD"}), 400

    try:
        email = sanitize_email(raw_email)
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_INPUT"}), 400

    try:
        history = mongodb_service.get_user_history(email)
        for record in history:
            if "created_at" in record and hasattr(record["created_at"], "isoformat"):
                record["created_at"] = record["created_at"].isoformat()
    except Exception as exc:
        logger.error("History retrieval failed: %s", exc)
        return jsonify({"error": "History unavailable.", "code": "MONGO_ERROR", "history": []}), 200

    return jsonify({"history": history, "count": len(history)}), 200


@history_bp.route("/history/<analysis_id>", methods=["GET"])
def get_analysis(analysis_id: str):
    """Retrieve a single full analysis by its ID.

    Args:
        analysis_id: MongoDB ObjectId string from the URL path.

    Returns:
        JSON with the full analysis document.
    """
    try:
        record = mongodb_service.get_analysis_by_id(analysis_id)
        if record is None:
            return jsonify({"error": "Analysis not found.", "code": "ANALYSIS_NOT_FOUND"}), 404
        if "created_at" in record and hasattr(record["created_at"], "isoformat"):
            record["created_at"] = record["created_at"].isoformat()
        return jsonify(record), 200
    except Exception as exc:
        logger.error("Analysis retrieval failed: %s", exc)
        return jsonify({"error": "Could not retrieve analysis.", "code": "MONGO_ERROR"}), 500
