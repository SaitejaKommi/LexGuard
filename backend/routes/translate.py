"""
translate.py - /api/translate route for multilingual support in LexGuard.
"""

import logging

from flask import Blueprint, request, jsonify

from ..services import translate_service
from ..utils.sanitizer import sanitize_text, sanitize_language_code
from ..utils.constants import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)
translate_bp = Blueprint("translate", __name__, url_prefix="/api")


@translate_bp.route("/translate", methods=["POST"])
def translate():
    """Translate a text string to the target language.

    Expects JSON body:
        - text (str): Text to translate (max 50000 chars)
        - target_lang (str): BCP-47 language code

    Returns:
        JSON with 'translated_text', 'source', 'success' keys.
    """
    body = request.get_json(silent=True) or {}
    raw_text = body.get("text", "")
    raw_lang = body.get("target_lang", "en")

    try:
        text = sanitize_text(raw_text)
        lang = sanitize_language_code(raw_lang)
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_INPUT"}), 400

    if lang not in SUPPORTED_LANGUAGES and not lang.startswith(tuple(SUPPORTED_LANGUAGES.keys())):
        return jsonify({
            "error": f"Language '{lang}' is not supported.",
            "code": "INVALID_INPUT",
            "supported": list(SUPPORTED_LANGUAGES.keys()),
        }), 400

    result = translate_service.translate_text(text, lang)
    return jsonify(result), 200
