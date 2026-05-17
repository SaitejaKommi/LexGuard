"""
gemini_service.py - Google Gemini API integration for LexGuard.

Provides six distinct AI-powered legal intelligence functions:
  1. Clause extraction and risk scoring (single combined prompt for efficiency)
  2. Plain language explanation
  3. Chat assistant with document context
  4. Contract comparison
  5. Negotiation recommendations
  6. Legal glossary definitions
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
    """Return the initialised Gemini model or raise if not configured."""
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

    Tries multiple strategies:
    1. Strip ```json ... ``` fences
    2. Find first { or [ to last } or ]
    3. Raise ValueError if still unparseable

    Args:
        raw: Raw text potentially wrapped in fences.

    Returns:
        Parsed Python object.

    Raises:
        ValueError: If no valid JSON can be found.
    """
    # Strategy 1: strip markdown code fences
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw)
    json_str = match.group(1) if match else raw.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Strategy 2: find outermost JSON object/array
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = json_str.find(start_char)
        end = json_str.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(json_str[start:end + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not parse Gemini JSON response. Raw (first 200 chars): {raw[:200]}")


def analyze_contract_full(document_text: str) -> dict:
    """Run complete single-pass contract analysis with Gemini.

    Single combined prompt for maximum efficiency — extracts clauses, scores
    risk, generates plain English, and computes overall score in ONE call.

    Args:
        document_text: Full extracted text of the contract.

    Returns:
        Dict matching the exact structure expected by the frontend:
        {
            "overall_score": int,
            "risk_level": str,
            "contract_type": str,
            "summary": str,
            "clauses": [...],
            "negotiation_priorities": [...],
            "red_flags": [...]
        }

    Raises:
        RuntimeError: On Gemini API failure.
        ValueError: If response cannot be parsed.
    """
    categories_str = ", ".join(CLAUSE_CATEGORIES)

    prompt = f"""You are an expert legal analyst with 20 years of experience in contract law. Analyze the following contract text thoroughly.

Your task: Extract every significant clause, assess risks, and provide plain-language explanations for a non-lawyer.

INSTRUCTIONS:
- Extract 8-15 of the most significant legal clauses
- For each clause, identify the risk level and explain it clearly
- Calculate an overall risk score from 0-100
- Return ONLY valid JSON — no markdown fences, no preamble, no explanation
- Do NOT wrap in ```json``` fences

RISK SCORING GUIDE:
- 80-100 = CRITICAL (severely unfair, dangerous, one-sided)
- 60-79 = HIGH (significant risk, needs negotiation)
- 40-59 = MEDIUM (some concern, review carefully)
- 20-39 = LOW (minor risk, standard language)
- 0-19 = SAFE (fair, standard, no concern)

CLAUSE CATEGORIES: {categories_str}

REQUIRED JSON STRUCTURE (return exactly this, with real data):
{{
  "overall_score": 75,
  "risk_level": "HIGH",
  "contract_type": "Employment Agreement",
  "summary": "Brief 2-3 sentence plain English summary of the contract's key risks",
  "clauses": [
    {{
      "id": "clause_1",
      "title": "Non-Compete Restriction",
      "category": "Non-Compete",
      "risk_level": "CRITICAL",
      "risk_score": 85,
      "original_text": "exact relevant clause text from the contract",
      "plain_english": "In simple words: what this clause means for you",
      "impact": "What this means for you practically — real world consequences",
      "recommendation": "Specific action to take: what to ask them to change or remove",
      "why_risky": "One sentence explaining the specific legal risk",
      "red_flags": ["flag 1", "flag 2"],
      "similarity_score": 0.45
    }}
  ],
  "negotiation_priorities": [
    "Top thing to negotiate first",
    "Second priority",
    "Third priority"
  ],
  "red_flags": [
    "Biggest concern 1",
    "Biggest concern 2",
    "Biggest concern 3"
  ]
}}

CONTRACT TEXT TO ANALYZE:
{document_text[:15000]}"""

    raw = _call_gemini(prompt)
    result = _extract_json(raw)

    # Validate and normalize
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object from contract analysis.")

    # Ensure all required top-level keys exist with defaults
    result.setdefault("overall_score", 50)
    result.setdefault("risk_level", "MEDIUM")
    result.setdefault("contract_type", "Legal Agreement")
    result.setdefault("summary", "Contract analyzed successfully.")
    result.setdefault("clauses", [])
    result.setdefault("negotiation_priorities", [])
    result.setdefault("red_flags", [])

    # Normalize each clause
    for i, clause in enumerate(result.get("clauses", [])):
        clause.setdefault("id", f"clause_{i + 1}")
        clause.setdefault("title", f"Clause {i + 1}")
        clause.setdefault("category", "Other")
        clause.setdefault("risk_level", "MEDIUM")
        clause.setdefault("risk_score", 50)
        clause.setdefault("original_text", "")
        clause.setdefault("plain_english", "No explanation available.")
        clause.setdefault("impact", "Review with your attorney.")
        clause.setdefault("recommendation", "Seek legal advice.")
        clause.setdefault("why_risky", "N/A")
        clause.setdefault("red_flags", [])
        clause.setdefault("similarity_score", 0.5)

    return result


# Keep legacy functions for backward compatibility with clause_extractor pipeline
def extract_clauses(document_text: str) -> list[dict]:
    """Use Gemini to identify and classify legal clauses in the document.

    Args:
        document_text: Full extracted text of the contract.

    Returns:
        List of clause dicts.
    """
    categories_str = ", ".join(CLAUSE_CATEGORIES)
    prompt = f"""You are an expert legal analyst. Analyze the following contract text and extract all significant legal clauses.

For each clause, return a JSON array where each element has:
- "clause_text": the exact clause text (max 500 chars)
- "category": one of [{categories_str}]
- "position": approximate character position in document (integer)
- "clause_title": a short 3-7 word title describing the clause

Extract 10-20 most significant clauses. Return ONLY valid JSON array, no other text, no markdown fences.

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
    """
    clauses_json = json.dumps(
        [{"clause_text": c.get("clause_text"), "category": c.get("category")} for c in clauses],
        indent=2,
    )
    prompt = f"""You are a senior legal risk analyst. Evaluate each of these contract clauses for risk.

For each clause return a JSON array where each element adds:
- "risk_level": one of ["CRITICAL", "HIGH", "MEDIUM", "LOW", "SAFE"]
- "risk_score": integer 0-100 (100 = most dangerous)
- "plain_english": 2-3 sentence plain English explanation as if talking to a friend
- "why_risky": one sentence explaining the specific risk
- "red_flags": array of 2-3 concise bullet point strings
- "what_to_watch": 1 sentence on what the person should watch out for

Return ONLY a JSON array matching the input order. No markdown, no extra text, no code fences.

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
                           "plain_english": "No risk detected.",
                           "why_risky": "N/A", "red_flags": [], "what_to_watch": "N/A"})
    return clauses


def generate_negotiation_recommendations(clauses: list[dict]) -> list[dict]:
    """Generate specific negotiation recommendations for high-risk clauses.

    Args:
        clauses: Fully scored clause list from score_risks().

    Returns:
        List of negotiation recommendation dicts for HIGH/CRITICAL clauses.
    """
    risky = [c for c in clauses if c.get("risk_level") in ("HIGH", "CRITICAL")]
    if not risky:
        return []

    risky_json = json.dumps(
        [{"clause_text": c.get("clause_text") or c.get("original_text", ""),
          "risk_level": c.get("risk_level"),
          "category": c.get("category")} for c in risky],
        indent=2,
    )
    prompt = f"""You are an expert contract negotiation attorney. For each high-risk clause, provide negotiation guidance.

Return a JSON array where each element has:
- "clause_title": short title identifying the clause
- "risk_level": the risk level
- "current_language": brief excerpt of the problematic clause (max 150 chars)
- "suggested_alternative": exact alternative contract language to propose
- "what_to_ask": what to ask the other party to change (1-2 sentences)
- "negotiation_tip": practical tip for the negotiation conversation
- "priority": "high", "medium", or "low"

Return ONLY valid JSON array. No markdown, no code fences.

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
        Comparison dict with keys: summary, differences, recommendation,
        overall_risk, clauses_altered, favorable_count, unfavorable_count.
    """
    prompt = f"""You are an expert legal analyst. Compare these two contracts and identify differences.

Return a JSON object with:
- "summary": 2-3 sentence overall comparison summary
- "overall_risk": "LOW", "MEDIUM", "HIGH", or "CRITICAL"
- "recommendation": which contract is more favorable ("Contract A", "Contract B", or "Neither") and why
- "clauses_altered": total number of clauses that differ
- "favorable_count": number of clauses more favorable in Contract B vs A
- "unfavorable_count": number of clauses less favorable in Contract B vs A
- "differences": array of objects, each with:
  - "clause_name": clause category/title
  - "original_text": relevant text from Contract A (max 200 chars)
  - "modified_text": relevant text from Contract B (max 200 chars)
  - "verdict": "favorable", "unfavorable", or "neutral"
  - "explanation": which is more favorable and why (1-2 sentences)

Return ONLY valid JSON. No markdown, no code fences.

CONTRACT A (first 6000 chars):
{text_a[:6000]}

CONTRACT B (first 6000 chars):
{text_b[:6000]}"""

    raw = _call_gemini(prompt)
    result = _extract_json(raw)
    result.setdefault("clauses_altered", len(result.get("differences", [])))
    result.setdefault("favorable_count", 0)
    result.setdefault("unfavorable_count", 0)
    result.setdefault("overall_risk", "MEDIUM")
    return result


def explain_legal_term(term: str) -> dict:
    """Explain a legal term in plain English using Gemini.

    Args:
        term: The legal term to define.

    Returns:
        Dict with keys: term, definition, example, related_terms.
    """
    prompt = f"""You are a plain-English legal educator. Explain the following legal term clearly for a non-lawyer.

LEGAL TERM: {term}

Return a JSON object with:
- "term": the exact term as given
- "definition": clear 2-3 sentence plain English definition (no jargon)
- "example": a concrete real-world example of this term in a contract (1-2 sentences)
- "related_terms": array of 3-5 related legal terms (strings only)
- "risk_note": one sentence on what to watch out for if you see this in a contract

Return ONLY valid JSON. No markdown, no code fences."""

    raw = _call_gemini(prompt)
    result = _extract_json(raw)
    result.setdefault("term", term)
    result.setdefault("definition", "Definition not available.")
    result.setdefault("example", "")
    result.setdefault("related_terms", [])
    result.setdefault("risk_note", "")
    return result


def generate_negotiation_from_analysis(clauses: list[dict]) -> list[dict]:
    """Generate negotiation recommendations from analyzed clauses.

    Args:
        clauses: Clause list from full analysis (may have risk_level field).

    Returns:
        List of negotiation recommendation dicts.
    """
    return generate_negotiation_recommendations(clauses)


def compute_overall_risk_score(clauses: list[dict]) -> int:
    """Compute a weighted overall risk score from clause risk levels.

    Args:
        clauses: List of scored clause dicts.

    Returns:
        Integer overall risk score from 0 to 100.
    """
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
