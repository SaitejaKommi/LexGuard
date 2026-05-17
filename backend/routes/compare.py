"""
compare.py - /api/compare route for contract comparison in LexGuard.

Accepts two uploaded documents, parses them, and uses Gemini to generate
a side-by-side clause-level comparison analysis.
"""

import logging

from flask import Blueprint, request, jsonify

from ..services import document_parser, gemini_service
from ..utils.sanitizer import sanitize_filename
from ..utils.constants import ERROR_CODES, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)
compare_bp = Blueprint("compare", __name__, url_prefix="/api")


def _parse_uploaded_file(*keys: str) -> tuple[str, str]:
    """Extract and parse a file from the multipart request by form key.

    Args:
        keys: Form field names to accept.

    Returns:
        Tuple of (extracted_text, safe_filename).

    Raises:
        ValueError: If the file is missing, invalid, or cannot be parsed.
    """
    key = next((candidate for candidate in keys if candidate in request.files), None)
    if key is None:
        raise ValueError(f"Missing file: one of {', '.join(keys)} is required.")

    file = request.files[key]
    filename = sanitize_filename(file.filename or "contract.txt")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}' for {key}.")

    data = file.read()
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File '{key}' exceeds the 10 MB size limit.")

    parsed = document_parser.parse_document(data, filename)
    return parsed["text"], filename


@compare_bp.route("/compare", methods=["POST"])
def compare():
    """Compare two uploaded contracts and return a Gemini analysis.

    Expects:
        multipart/form-data with:
            - file_a: First contract (PDF/DOCX/TXT)
            - file_b: Second contract (PDF/DOCX/TXT)

    Returns:
        JSON with comparison summary, differences array, and recommendation.
    """
    try:
        text_a, name_a = _parse_uploaded_file("file_a", "file1")
        text_b, name_b = _parse_uploaded_file("file_b", "file2")
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_INPUT"}), 400

    try:
        comparison = gemini_service.compare_contracts(text_a, text_b)
    except (RuntimeError, ValueError) as exc:
        message_text = str(exc).lower()
        if any(token in message_text for token in ("not initial", "not configured", "model")):
            logger.warning("Comparison failed; using fallback comparison: %s", exc)
            comparison = gemini_service._fallback_compare(text_a, text_b)
        else:
            logger.error("Comparison failed: %s", exc)
            return jsonify({"error": str(exc), "code": "GEMINI_ERROR"}), 502

    return jsonify({
        "contract_a": name_a,
        "contract_b": name_b,
        "comparison": comparison,
    }), 200
