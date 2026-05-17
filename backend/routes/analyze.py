"""
analyze.py - /api/analyze route for LexGuard.

Accepts multipart file uploads, parses documents, runs the full AI analysis
pipeline, stores results in MongoDB, and returns structured JSON.
"""

import logging
import uuid

from flask import Blueprint, request, jsonify, session, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from ..services import document_parser, clause_extractor
from ..services import mongodb_service, firebase_service
from ..utils.sanitizer import sanitize_filename, sanitize_email
from ..utils.constants import (
    MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS, ERROR_CODES, ANALYSIS_CACHE_TTL
)

logger = logging.getLogger(__name__)
analyze_bp = Blueprint("analyze", __name__, url_prefix="/api")


def _get_session_id() -> str:
    """Retrieve or create a unique session ID for the current request.

    Returns:
        Session ID string.
    """
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


def _validate_upload(file) -> tuple[bytes, str]:
    """Validate uploaded file size, extension, and return raw bytes.

    Args:
        file: Werkzeug FileStorage object from the request.

    Returns:
        Tuple of (file_bytes, safe_filename).

    Raises:
        ValueError: If validation fails.
    """
    filename = sanitize_filename(file.filename or "upload.txt")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(ERROR_CODES["INVALID_FILE_TYPE"])

    data = file.read()
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValueError(ERROR_CODES["FILE_TOO_LARGE"])
    if len(data) == 0:
        raise ValueError("Uploaded file is empty.")

    return data, filename


@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    """Analyze an uploaded contract document end-to-end.

    Expects:
        multipart/form-data with:
            - file: PDF, DOCX, or TXT file (max 10 MB)
            - email (optional): user email for history storage

    Returns:
        JSON with full analysis including clauses, risk scores, and recommendations.
    """
    if "file" not in request.files:
        return jsonify({"error": ERROR_CODES["MISSING_FIELD"], "code": "MISSING_FIELD",
                        "details": {"field": "file"}}), 400

    file = request.files["file"]
    user_email = request.form.get("email", "anonymous@lexguard.ai")
    try:
        user_email = sanitize_email(user_email)
    except ValueError:
        user_email = "anonymous@lexguard.ai"

    try:
        data, filename = _validate_upload(file)
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_FILE_TYPE"}), 400

    try:
        parsed = document_parser.parse_document(data, filename)
    except (ValueError, ImportError) as exc:
        logger.error("Document parsing failed: %s", exc)
        return jsonify({"error": str(exc), "code": "PARSE_ERROR"}), 422

    doc_text = parsed["text"]
    doc_hash = mongodb_service.compute_doc_hash(doc_text)

    cached = None
    try:
        cached = mongodb_service.get_analysis_by_hash(doc_hash)
    except Exception:
        pass

    if cached:
        logger.info("Returning cached analysis for hash %s.", doc_hash[:8])
        return jsonify({"cached": True, **cached}), 200

    try:
        pipeline_result = clause_extractor.run_full_extraction_pipeline(doc_text)
    except RuntimeError as exc:
        logger.warning("Analysis pipeline failed; using fallback analysis: %s", exc)
        from ..services import gemini_service

        pipeline_result = gemini_service._fallback_analysis(doc_text)

    try:
        mongodb_service.upsert_user(user_email)
        analysis_id = mongodb_service.save_analysis(
            user_email=user_email,
            filename=filename,
            doc_hash=doc_hash,
            risk_score=pipeline_result["overall_risk_score"],
            clauses=pipeline_result["clauses"],
            summary=pipeline_result["summary"],
            contract_type=pipeline_result.get("contract_type", "Legal Agreement"),
            raw_text_snippet=doc_text[:500],
        )
        firebase_service.backup_analysis_to_firestore(
            analysis_id, user_email,
            pipeline_result["overall_risk_score"],
            pipeline_result["summary"],
        )
    except Exception as exc:
        logger.warning("Storage failed (non-critical): %s", exc)
        analysis_id = doc_hash[:16]

    session["current_doc_text"] = doc_text[:8000]
    session["current_clauses_summary"] = str(pipeline_result["clauses"])[:3000]
    session["session_id"] = _get_session_id()

    return jsonify({
        "analysis_id": analysis_id,
        "filename": filename,
        "file_type": parsed["file_type"],
        "page_count": parsed["page_count"],
        "char_count": parsed["char_count"],
        "overall_score": pipeline_result.get("overall_score", pipeline_result.get("overall_risk_score", 0)),
        "overall_risk_score": pipeline_result.get("overall_risk_score", pipeline_result.get("overall_score", 0)),
        "risk_level": pipeline_result.get("risk_level") or _score_to_level(pipeline_result.get("overall_score", pipeline_result.get("overall_risk_score", 0))),
        "contract_type": pipeline_result.get("contract_type", "Legal Agreement"),
        "risk_distribution": pipeline_result["risk_distribution"],
        "clauses": pipeline_result["clauses"],
        "negotiation_recommendations": pipeline_result["negotiation_recommendations"],
        "negotiation_priorities": pipeline_result.get("negotiation_priorities", []),
        "red_flags": pipeline_result.get("red_flags", []),
        "summary": pipeline_result["summary"],
        "cached": False,
    }), 200


def _score_to_level(score: int) -> str:
    """Convert numeric risk score to level label."""
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    if score >= 20:
        return "LOW"
    return "SAFE"
