"""
chat.py - /api/chat route for LexGuard AI legal assistant.

Maintains per-session conversation history in MongoDB and forwards
user questions to Gemini with full document context.
"""

import logging
import uuid

from flask import Blueprint, request, jsonify, session

from ..services import gemini_service, mongodb_service
from ..utils.sanitizer import sanitize_chat_message
from ..utils.constants import ERROR_CODES

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__, url_prefix="/api")


def _get_session_id() -> str:
    """Retrieve or create a session ID.

    Returns:
        Session ID string.
    """
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """Answer a user question about the currently analyzed contract.

    Expects JSON body:
        - message (str): User's question (max 1000 chars)
        - email (optional str): User email for persistence

    Returns:
        JSON with 'response' key containing Gemini's answer.
    """
    body = request.get_json(silent=True) or {}
    raw_message = body.get("message", "")
    incoming_session_id = body.get("session_id")
    document_context = body.get("document_context", "")

    try:
        message = sanitize_chat_message(raw_message)
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_INPUT"}), 400

    if incoming_session_id:
        session["session_id"] = str(incoming_session_id)

    doc_text = document_context or session.get("current_doc_text", "")
    clauses_summary = session.get("current_clauses_summary", "")
    if document_context and not clauses_summary:
        clauses_summary = document_context[:3000]
        session["current_doc_text"] = document_context[:8000]
        session["current_clauses_summary"] = clauses_summary

    if not doc_text:
        return jsonify({
            "error": "No document analyzed yet. Please upload a contract first.",
            "code": "SESSION_NOT_FOUND",
        }), 400

    session_id = _get_session_id()

    try:
        history = mongodb_service.get_chat_history(session_id, limit=10)
    except Exception:
        history = []

    try:
        answer = gemini_service.chat_with_document(
            doc_text, clauses_summary, history, message
        )
    except RuntimeError as exc:
        message_text = str(exc).lower()
        if any(token in message_text for token in ("not initial", "not configured", "model")):
            logger.warning("Chat failed; using fallback answer: %s", exc)
            answer = gemini_service._fallback_chat(doc_text, clauses_summary, history, message)
        else:
            logger.error("Chat failed: %s", exc)
            return jsonify({"error": str(exc), "code": "GEMINI_ERROR"}), 502

    try:
        mongodb_service.save_chat_message(session_id, "user", message)
        mongodb_service.save_chat_message(session_id, "assistant", answer)
    except Exception as exc:
        logger.warning("Chat history save failed: %s", exc)

    return jsonify({"response": answer, "session_id": session_id}), 200
