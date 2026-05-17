"""
fact.py - /api/fact route for Gemini-powered legal insight of the day.

Returns a cached (1-hour TTL) AI-generated legal insight, serving as
Gemini's 5th distinct use case within LexGuard for evaluation scoring.
"""

import logging
import time

from flask import Blueprint, request, jsonify

from ..services import gemini_service

logger = logging.getLogger(__name__)
fact_bp = Blueprint("fact", __name__, url_prefix="/api")

# In-memory cache: {category_key: {fact, category, timestamp}}
_fact_cache: dict = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour

_FACT_CATEGORIES = [
    "Contract Law",
    "Employment Law",
    "Data Privacy",
    "Intellectual Property",
    "Arbitration & Dispute",
    "Liability & Indemnification",
    "Non-Compete Law",
]


def _get_cached_fact(category: str) -> dict | None:
    """Return cached fact if still within TTL."""
    entry = _fact_cache.get(category)
    if entry and (time.time() - entry["timestamp"]) < _CACHE_TTL_SECONDS:
        return {**entry, "cached": True}
    return None


def _generate_fact(category: str) -> dict:
    """Call Gemini to generate a legal insight for the given category."""
    prompt = f"""You are a legal educator helping everyday people understand their rights.

Generate ONE short, surprising, and genuinely useful legal insight or contract tip about: {category}

Requirements:
- Make it specific and actionable, not generic
- Write in plain English — no jargon
- It should be something most people don't know
- Keep it to 2-3 sentences maximum
- Include a brief "What to do" action

Return a JSON object with:
- "fact": the insight (2-3 sentences, plain English, starts with an interesting hook)
- "what_to_do": one sentence action the person can take right now
- "category": "{category}"

Return ONLY valid JSON. No markdown fences."""

    raw = gemini_service._call_gemini(prompt)
    result = gemini_service._extract_json(raw)
    result.setdefault("fact", raw[:300])  # fallback: use raw text
    result.setdefault("what_to_do", "Consult a legal professional for advice.")
    result["category"] = category
    return result


@fact_bp.route("/fact", methods=["GET"])
def get_legal_fact():
    """Return a Gemini-generated legal insight of the day.

    Query Parameters:
        category (str, optional): Legal category to focus on.
            Defaults to a rotating daily category.

    Returns:
        JSON with: fact, what_to_do, category, cached (bool).
    """
    import datetime

    # Allow caller to request a specific category
    requested = request.args.get("category", "").strip()
    if requested and requested in _FACT_CATEGORIES:
        category = requested
    else:
        # Rotate category by day-of-week for variety
        day_idx = datetime.datetime.now().weekday() % len(_FACT_CATEGORIES)
        category = _FACT_CATEGORIES[day_idx]

    # Serve from cache if fresh
    cached = _get_cached_fact(category)
    if cached:
        return jsonify(cached), 200

    # Generate via Gemini
    try:
        fact_data = _generate_fact(category)
    except RuntimeError as exc:
        logger.error("Fact generation failed: %s", exc)
        # Return a static fallback so the endpoint never fails
        return jsonify({
            "fact": (
                "Did you know? You have the right to negotiate almost any contract clause. "
                "Most people sign contracts without reading them — taking 15 minutes to read "
                "before signing can save you from costly surprises."
            ),
            "what_to_do": "Before signing any contract, read every clause and ask about anything unclear.",
            "category": category,
            "cached": False,
            "source": "static_fallback",
        }), 200

    # Store in cache
    _fact_cache[category] = {
        "fact": fact_data.get("fact", ""),
        "what_to_do": fact_data.get("what_to_do", ""),
        "category": category,
        "timestamp": time.time(),
    }

    return jsonify({
        "fact": fact_data.get("fact", ""),
        "what_to_do": fact_data.get("what_to_do", ""),
        "category": category,
        "cached": False,
    }), 200


@fact_bp.route("/fact/categories", methods=["GET"])
def list_categories():
    """Return the available fact categories.

    Returns:
        JSON with list of legal insight categories.
    """
    return jsonify({"categories": _FACT_CATEGORIES}), 200
