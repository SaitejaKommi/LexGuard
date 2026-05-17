"""
gemini_service.py - Google Gemini API integration for LexGuard.

Provides six distinct AI-powered legal intelligence functions:
  1. Clause extraction and classification
  2. Risk scoring per clause
  3. Plain language explanation
  4. Chat assistant with document context
  5. Contract comparison
  6. Negotiation recommendations
"""

import json
import logging
import re
from typing import Any, Optional

import google.generativeai as genai

from ..utils.constants import (
    GEMINI_MODEL,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_TEMPERATURE,
    CLAUSE_CATEGORIES,
    RISK_LEVELS,
)

logger = logging.getLogger(__name__)

_model: Optional[genai.GenerativeModel] = None


def init_gemini(api_key: str) -> None:
    """Configure the Gemini SDK with the provided API key.

    Args:
        api_key: Google Gemini API key from environment.
    """
    global _model
    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config={
            "temperature": GEMINI_TEMPERATURE,
            "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
        },
    )
    logger.info("Gemini model '%s' initialised.", GEMINI_MODEL)


def _get_model() -> genai.GenerativeModel:
    """Return the initialised Gemini model or raise if not configured.

    Returns:
        Configured GenerativeModel instance.

    Raises:
        RuntimeError: If init_gemini has not been called.
    """
    if _model is None:
        raise RuntimeError("Gemini is not initialised. Call init_gemini() first.")
    return _model


def _call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the text response.

    Args:
        prompt: Full prompt string to send.

    Returns:
        Raw text response from Gemini.

    Raises:
        RuntimeError: On API failure.
    """
    try:
        model = _get_model()
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc)
        raise RuntimeError(f"Gemini API error: {exc}") from exc


def _extract_json(raw: str) -> Any:
    """Extract JSON from a Gemini response that may have markdown fences.

    Args:
        raw: Raw text potentially wrapped in ```json ... ``` fences.

    Returns:
        Parsed Python object.

    Raises:
        ValueError: If no valid JSON can be found.
    """
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw)
    json_str = match.group(1) if match else raw.strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse Gemini JSON response: {exc}") from exc


def extract_clauses(document_text: str) -> list[dict]:
    """Use Gemini to identify and classify legal clauses in the document.

    Args:
        document_text: Full extracted text of the contract.

    Returns:
        List of clause dicts with keys: clause_text, category, position.

    Raises:
        RuntimeError: On Gemini API failure.
        ValueError: If the response cannot be parsed as JSON.
    """
    categories_str = ", ".join(CLAUSE_CATEGORIES)
    prompt = f"""You are an expert legal analyst. Analyze the following contract text and extract all significant legal clauses.

For each clause, return a JSON array where each element has:
- "clause_text": the exact clause text (max 500 chars)
- "category": one of [{categories_str}]
- "position": approximate character position in document (integer)
- "clause_title": a short 3-7 word title describing the clause

Extract 10-20 most significant clauses. Return ONLY valid JSON array, no other text.

CONTRACT TEXT:
{document_text[:15000]}"""

    raw = _call_gemini(prompt)
    clauses = _extract_json(raw)
    if not isinstance(clauses, list):
        raise ValueError("Expected a JSON array of clauses.")
    return clauses


def score_risks(clauses: list[dict]) -> list[dict]:
    """Analyse risk level and generate explanations for each clause.

    Args:
        clauses: List of clause dicts from extract_clauses().

    Returns:
        Updated clause list with added risk fields per clause.

    Raises:
        RuntimeError: On Gemini API failure.
        ValueError: If the response cannot be parsed as JSON.
    """
    clauses_json = json.dumps(
        [{"clause_text": c.get("clause_text"), "category": c.get("category")} for c in clauses],
        indent=2,
    )
    prompt = f"""You are a senior legal risk analyst. Evaluate each of these contract clauses for risk.

For each clause return a JSON array where each element adds:
- "risk_level": one of ["CRITICAL", "HIGH", "MEDIUM", "LOW", "SAFE"]
- "risk_score": integer 0-100 (100 = most dangerous)
- "plain_explanation": 2-3 sentence plain English explanation as if talking to a friend
- "why_risky": one sentence explaining the specific risk
- "red_flags": array of 2-3 concise bullet point strings
- "what_to_watch": 1 sentence on what the person should watch out for

Return ONLY a JSON array matching the input order. No markdown, no extra text.

CLAUSES:
{clauses_json}"""

    raw = _call_gemini(prompt)
    scored = _extract_json(raw)
    if not isinstance(scored, list) or len(scored) != len(clauses):
        logger.warning("Gemini risk scoring returned mismatched count; using partial results.")
        scored = scored[: len(clauses)]

    for i, clause in enumerate(clauses):
        if i < len(scored):
            clause.update(scored[i])
        else:
            clause.update({"risk_level": "SAFE", "risk_score": 0,
                           "plain_explanation": "No risk detected.",
                           "why_risky": "N/A", "red_flags": [], "what_to_watch": "N/A"})
    return clauses


def generate_negotiation_recommendations(clauses: list[dict]) -> list[dict]:
    """Generate specific negotiation recommendations for high-risk clauses.

    Args:
        clauses: Fully scored clause list from score_risks().

    Returns:
        List of negotiation recommendation dicts for HIGH/CRITICAL clauses.

    Raises:
        RuntimeError: On Gemini API failure.
    """
    risky = [c for c in clauses if c.get("risk_level") in ("HIGH", "CRITICAL")]
    if not risky:
        return []

    risky_json = json.dumps(
        [{"clause_text": c.get("clause_text"), "risk_level": c.get("risk_level"),
          "category": c.get("category")} for c in risky],
        indent=2,
    )
    prompt = f"""You are an expert contract negotiation attorney. For each high-risk clause, provide negotiation guidance.

Return a JSON array where each element has:
- "original_clause": brief excerpt of the problematic clause (max 150 chars)
- "alternative_language": exact alternative contract language to propose
- "what_to_ask": what to ask the other party to change (1-2 sentences)
- "reasonable_ask": is this a reasonable negotiation request? (true/false)
- "negotiation_tip": practical tip for the negotiation conversation

Return ONLY valid JSON array. No markdown.

HIGH-RISK CLAUSES:
{risky_json}"""

    raw = _call_gemini(prompt)
    return _extract_json(raw)


def chat_with_document(
    document_text: str,
    clauses_summary: str,
    conversation_history: list[dict],
    user_message: str,
) -> str:
    """Answer a user question about a specific contract using Gemini.

    Args:
        document_text: Extracted contract text (truncated for context).
        clauses_summary: JSON summary of extracted clauses.
        conversation_history: List of {role, content} dicts.
        user_message: The user's current question.

    Returns:
        Gemini's answer as a plain string.

    Raises:
        RuntimeError: On Gemini API failure.
    """
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in conversation_history[-6:]
    )
    prompt = f"""You are LexGuard AI, an expert legal assistant. You have analyzed a contract and must answer the user's question about it.

CONTRACT CONTEXT (first 8000 chars):
{document_text[:8000]}

EXTRACTED CLAUSES SUMMARY:
{clauses_summary[:3000]}

CONVERSATION HISTORY:
{history_text}

USER QUESTION: {user_message}

Answer helpfully in plain language. Be specific, cite clause text when relevant, and always add: "Note: This is AI analysis, not legal advice. Consult a licensed attorney for legal decisions."

Answer:"""

    return _call_gemini(prompt)


def compare_contracts(text_a: str, text_b: str) -> dict:
    """Compare two contracts and identify key differences.

    Args:
        text_a: Extracted text of Contract A.
        text_b: Extracted text of Contract B.

    Returns:
        Comparison dict with keys: summary, differences, recommendation.

    Raises:
        RuntimeError: On Gemini API failure.
        ValueError: If response cannot be parsed.
    """
    prompt = f"""You are an expert legal analyst. Compare these two contracts and identify differences.

Return a JSON object with:
- "summary": 2-3 sentence overall comparison summary
- "recommendation": which contract is more favorable ("Contract A", "Contract B", or "Neither") and why
- "differences": array of objects, each with:
  - "category": clause category
  - "contract_a_text": relevant text from Contract A (max 200 chars)
  - "contract_b_text": relevant text from Contract B (max 200 chars)
  - "analysis": which is more favorable and why (1-2 sentences)
  - "winner": "Contract A", "Contract B", or "Tie"

Return ONLY valid JSON. No markdown.

CONTRACT A (first 6000 chars):
{text_a[:6000]}

CONTRACT B (first 6000 chars):
{text_b[:6000]}"""

    raw = _call_gemini(prompt)
    return _extract_json(raw)


def compute_overall_risk_score(clauses: list[dict]) -> int:
    """Compute a weighted overall risk score from clause risk levels.

    Args:
        clauses: List of scored clause dicts.

    Returns:
        Integer overall risk score from 0 to 100.
    """
    from ..utils.constants import RISK_LEVEL_WEIGHTS

    if not clauses:
        return 0

    weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "SAFE": 0}
    total_weight = 0
    weighted_score = 0.0

    for clause in clauses:
        level = clause.get("risk_level", "SAFE")
        score = clause.get("risk_score", 0)
        w = weights.get(level, 0)
        total_weight += w + 1
        weighted_score += score * (w + 1)

    if total_weight == 0:
        return 0
    return min(100, int(weighted_score / total_weight))


def generate_analysis_summary(
    document_text: str, overall_risk_score: int, clauses: list[dict]
) -> str:
    """Generate a concise one-paragraph analysis summary.

    Args:
        document_text: Extracted contract text.
        overall_risk_score: Computed overall risk score.
        clauses: List of scored clauses.

    Returns:
        Summary paragraph string.
    """
    critical_count = sum(1 for c in clauses if c.get("risk_level") == "CRITICAL")
    high_count = sum(1 for c in clauses if c.get("risk_level") == "HIGH")
    prompt = f"""In 3-4 sentences, summarize this contract's risk profile for a non-lawyer.
Overall risk score: {overall_risk_score}/100
Critical clauses: {critical_count}, High risk clauses: {high_count}
Total clauses analyzed: {len(clauses)}
Contract excerpt: {document_text[:2000]}

Provide plain English summary. Start with the risk level. End with a clear recommendation action."""

    try:
        return _call_gemini(prompt)
    except Exception as exc:
        logger.warning("Summary generation failed: %s", exc)
        return f"Contract analyzed with overall risk score of {overall_risk_score}/100."
