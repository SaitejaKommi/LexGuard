"""
tts.py - /api/tts route for text-to-speech synthesis in LexGuard.
"""

import logging

from flask import Blueprint, request, jsonify

from ..services import tts_service
from ..utils.sanitizer import sanitize_text, sanitize_language_code
from ..utils.constants import TTS_LANGUAGE_CODE, TTS_VOICE_NAME

logger = logging.getLogger(__name__)
tts_bp = Blueprint("tts", __name__, url_prefix="/api")


@tts_bp.route("/tts", methods=["POST"])
def tts():
    """Synthesize speech from the provided text.

    Expects JSON body:
        - text (str): Text to speak (max 5000 chars)
        - language_code (optional str): BCP-47 language code (default 'en-US')
        - voice_name (optional str): Google TTS voice name

    Returns:
        JSON with 'audio_base64', 'source', 'success', 'fallback_text' keys.
    """
    body = request.get_json(silent=True) or {}
    raw_text = body.get("text", "")
    raw_lang = body.get("language_code", TTS_LANGUAGE_CODE)
    voice_name = body.get("voice_name", TTS_VOICE_NAME)

    try:
        text = sanitize_text(raw_text, max_length=5000)
        lang = sanitize_language_code(raw_lang.split("-")[0])
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_INPUT"}), 400

    result = tts_service.synthesize_speech(text, raw_lang, voice_name)
    return jsonify(result), 200
