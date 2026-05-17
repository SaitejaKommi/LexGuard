"""
health.py - /api/health endpoint for LexGuard service health monitoring.
"""

import logging

from flask import Blueprint, jsonify

from ..services import mongodb_service, gemini_service, embedding_service, firebase_service
from ..utils.constants import APP_VERSION

logger = logging.getLogger(__name__)
health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health():
    """Return the health status of all LexGuard services.

    Returns:
        JSON with status 'ok', version, and per-service health booleans.
    """
    mongo_ok = False
    try:
        mongo_ok = mongodb_service.health_check()
    except Exception:
        pass

    gemini_ok = gemini_service._model is not None
    embedder_ok = embedding_service.is_embedder_available()
    firebase_ok = firebase_service.is_firebase_available()

    services = {
        "mongodb": mongo_ok,
        "gemini": gemini_ok,
        "embedding": embedder_ok,
        "firebase": firebase_ok,
    }

    overall = "ok" if gemini_ok else "degraded"

    return jsonify({
        "status": overall,
        "version": APP_VERSION,
        "services": services,
    }), 200
