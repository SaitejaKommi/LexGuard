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


_GEMINI_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]


def init_gemini(api_key: str) -> None:
    """Configure the Gemini SDK and initialise the best available model.

    Configures the Gemini SDK for lazy use at request time. Startup must not
    fail if credentials are missing or if the API is temporarily unavailable.

    Args:
        api_key: Google Gemini API key from environment.
    """
    global _model
    if not api_key:
        _model = None
        logger.warning("GEMINI_API_KEY not set; AI features disabled.")
        return

    genai.configure(api_key=api_key)
    try:
        _model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": GEMINI_TEMPERATURE,
                "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
            },
        )
        logger.info("Gemini model '%s' configured.", GEMINI_MODEL)
    except Exception as exc:
        _model = None
        logger.warning("Gemini initialization failed: %s. AI features disabled.", exc)


def _get_model() -> genai.GenerativeModel:
    """Return the initialised Gemini model or raise if not configured."""
    if _model is None:
        raise RuntimeError("Gemini is not initialised. Call init_gemini() first.")
    return _model


def _call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the text response.

    On model-not-found errors, automatically retries with the next available
    model in the fallback chain.

    Args:
        prompt: Full prompt string to send.

    Returns:
        Raw text response from Gemini.

    Raises:
        RuntimeError: On API failure after all retries.
    """
    global _model
    model = _get_model()

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        err_str = str(exc).lower()
        # If this is a model availability error, try fallbacks
        if any(kw in err_str for kw in ("not found", "404", "deprecated", "invalid")):
            logger.warning("Current model failed (%s); attempting fallback models.", exc)
            current_name = model.model_name if hasattr(model, "model_name") else ""
            for fallback_name in _GEMINI_MODELS:
                if fallback_name == current_name:
                    continue
                try:
                    fallback = genai.GenerativeModel(
                        model_name=fallback_name,
                        generation_config={
                            "temperature": GEMINI_TEMPERATURE,
                            "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
                        },
                    )
                    response = fallback.generate_content(prompt)
                    _model = fallback  # Persist the working model
                    logger.info("Switched to fallback Gemini model '%s'.", fallback_name)
                    return response.text
                except Exception as fb_exc:
                    logger.warning("Fallback model '%s' also failed: %s", fallback_name, fb_exc)
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


def _score_to_level(score: int) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    if score >= 20:
        return "LOW"
    return "SAFE"


def _normalize_clause_category(text: str) -> str:
    lowered = text.lower()
    mapping = [
        ("non-compete", "NonCompete"),
        ("non compete", "NonCompete"),
        ("indemn", "Indemnification"),
        ("arbitr", "Arbitration"),
        ("confidential", "Confidentiality"),
        ("liabil", "Liability"),
        ("termination", "Termination"),
        ("intellectual property", "IPRights"),
        ("copyright", "IPRights"),
        ("privacy", "Privacy"),
        ("data", "Privacy"),
        ("renew", "Renewal"),
        ("auto-renew", "Renewal"),
        ("salary", "Financial"),
        ("payment", "Financial"),
        ("governing law", "GoverningLaw"),
    ]
    for needle, category in mapping:
        if needle in lowered:
            return category
    return "Other"


def _analyze_clause_locally(clause_text: str) -> dict:
    lowered = clause_text.lower()
    score = 20
    reasons: list[str] = []
    recommendations: list[str] = []

    keyword_rules = [
        ("non-compete", 92, "This limits where and how you can work after the contract ends.", "Ask to shorten the duration, narrow the industry scope, and limit the geography."),
        ("indemn", 88, "You may be paying for losses even when you are not at fault.", "Limit indemnity to your own proven negligence or misconduct."),
        ("arbitr", 76, "This can force disputes into a private process with fewer appeal rights.", "Ask for a neutral arbitrator, shared fees, and a court option for urgent relief."),
        ("liabil", 74, "This can cap the other side's responsibility while leaving your exposure open.", "Negotiate a mutual liability cap and carve-outs for intentional harm only."),
        ("confidential", 60, "This may restrict sharing information for a long time.", "Add a sunset clause and carve out public or already-known information."),
        ("intellectual property", 84, "This may assign everything you create to the other side.", "Limit the assignment to work created using company resources during the contract term."),
        ("privacy", 78, "This may allow broad collection or use of personal data.", "Narrow the data types, purpose, and sharing permissions."),
        ("data", 78, "This may allow broad collection or use of personal data.", "Narrow the data types, purpose, and sharing permissions."),
        ("renew", 68, "This may auto-renew the agreement or make cancellation difficult.", "Add a clear cancellation window and written notice requirement."),
        ("termination", 66, "This may let one side end the contract without fair notice or severance.", "Ask for mutual notice periods and a cause-based termination standard."),
        ("payment", 55, "This clause affects money, billing, or timing obligations.", "Confirm payment timing, late fees, and any refund rights."),
        ("salary", 55, "This clause affects money, billing, or timing obligations.", "Confirm payment timing, late fees, and any refund rights."),
        ("governing law", 42, "This determines which jurisdiction's law will apply.", "Prefer a neutral or mutually acceptable jurisdiction."),
    ]

    for needle, candidate_score, reason, recommendation in keyword_rules:
        if needle in lowered:
            score = max(score, candidate_score)
            reasons.append(reason)
            recommendations.append(recommendation)

    if len(clause_text) > 800:
        score = max(score, 45)
        reasons.append("This section is unusually long and may hide additional obligations.")

    risk_level = _score_to_level(score)
    title_words = clause_text.strip().split()
    title = " ".join(title_words[:6]).rstrip(".,;") if title_words else "Clause"
    category = _normalize_clause_category(clause_text)
    plain = reasons[0] if reasons else "This appears to be standard contract language."
    impact = reasons[0] if reasons else "This is unlikely to materially change your obligations."
    recommendation = recommendations[0] if recommendations else "Review this clause with a lawyer before signing."

    return {
        "id": "",
        "title": title,
        "category": category,
        "risk_level": risk_level,
        "risk_score": score,
        "original_text": clause_text[:500],
        "plain_english": plain,
        "impact": impact,
        "recommendation": recommendation,
        "why_risky": plain,
        "red_flags": reasons[:3] if reasons else ["Standard language"],
        "similarity_score": 45 if risk_level in {"HIGH", "CRITICAL"} else 80,
    }


def _split_local_clauses(document_text: str) -> list[str]:
    text = document_text.strip()
    if not text:
        return []

    parts = re.split(r"\n(?=\s*(?:\d+\.|\d+\)|[A-Z][A-Z\s]{3,}:))", text)
    chunks = [part.strip() for part in parts if part.strip()]
    if len(chunks) > 1:
        return chunks[:15]

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    return paragraphs[:15]


def _fallback_analysis(document_text: str) -> dict:
    clauses = [_analyze_clause_locally(chunk) for chunk in _split_local_clauses(document_text)]
    if not clauses:
        clauses = [_analyze_clause_locally(document_text[:1000] or "General contract terms.")]

    for idx, clause in enumerate(clauses, start=1):
        clause["id"] = f"clause_{idx}"

    overall_score = compute_overall_risk_score(clauses)
    risk_level = _score_to_level(overall_score)
    red_flags = []
    for clause in clauses:
        red_flags.extend(clause.get("red_flags", []))
    red_flags = list(dict.fromkeys(red_flags))[:5]
    negotiation_priorities = [
        clause["recommendation"]
        for clause in sorted(clauses, key=lambda c: c.get("risk_score", 0), reverse=True)
        if clause.get("risk_level") in {"HIGH", "CRITICAL"}
    ][:3]
    if not negotiation_priorities:
        negotiation_priorities = ["Confirm the key obligations and any cancellation rights."]

    return {
        "overall_score": overall_score,
        "overall_risk_score": overall_score,
        "risk_level": risk_level,
        "contract_type": "Employment Agreement" if "employment" in document_text.lower() else "Legal Agreement",
        "summary": f"Fallback analysis identified {len(clauses)} clause(s) with an overall {risk_level.lower()} risk profile.",
        "clauses": clauses,
        "negotiation_priorities": negotiation_priorities,
        "red_flags": red_flags,
        "risk_distribution": {
            level: sum(1 for clause in clauses if clause.get("risk_level") == level)
            for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "SAFE"]
        },
        "negotiation_recommendations": [
            {
                "clause_title": clause.get("title", "Clause"),
                "risk_level": clause.get("risk_level", "MEDIUM"),
                "current_language": clause.get("original_text", "")[:150],
                "suggested_alternative": clause.get("recommendation", "Review with counsel."),
                "what_to_ask": clause.get("recommendation", "Review with counsel."),
                "negotiation_tip": "Use the clause's business impact to justify a narrower alternative.",
                "priority": "high" if clause.get("risk_level") in {"HIGH", "CRITICAL"} else "medium",
            }
            for clause in clauses
            if clause.get("risk_level") in {"HIGH", "CRITICAL"}
        ],
    }


def _fallback_glossary(term: str) -> dict:
    term_key = term.strip().lower()
    definitions = {
        "indemnification": (
            "A promise to compensate the other side for certain losses or claims.",
            "If a vendor's mistake causes a lawsuit, an indemnification clause may require one side to cover the cost.",
            "liability",
            "damages",
            "hold harmless",
            "Watch for one-sided or unlimited indemnification obligations.",
        ),
        "arbitration": (
            "A private dispute process instead of going to court.",
            "Two companies may require disputes to be heard by an arbitrator rather than a judge.",
            "mediation",
            "class action waiver",
            "forum selection",
            "You may lose some court rights, including a jury trial.",
        ),
        "non-compete": (
            "A restriction that limits where you can work or compete after the contract ends.",
            "An employee may be barred from working in the same industry for a period of time after resignation.",
            "restraint of trade",
            "garden leave",
            "employment agreement",
            "Overbroad non-competes can be hard to challenge after you sign.",
        ),
    }
    definition, example, *rest = definitions.get(
        term_key,
        (
            f"A legal term related to {term_key}.",
            f"This term describes a contract rule that affects {term_key}.",
            "contract",
            "liability",
            "risk",
            "Watch for vague wording and hidden obligations.",
        ),
    )
    return {
        "term": term,
        "definition": definition,
        "example": example,
        "related_terms": list(rest[:3]),
        "risk_note": rest[3] if len(rest) > 3 else "Watch for vague wording and hidden obligations.",
    }


def _fallback_chat(document_text: str, clauses_summary: str, conversation_history: list[dict], user_message: str) -> str:
    context = f"{document_text}\n{clauses_summary}".lower()
    highlights = []
    if "non-compete" in context or "non compete" in context:
        highlights.append("The non-compete looks like one of the highest-risk provisions because it can limit future work options.")
    if "indemn" in context:
        highlights.append("The indemnification language may require you to pay for claims even when you are not at fault.")
    if "arbitr" in context:
        highlights.append("The arbitration clause may reduce your ability to sue in court or appeal a decision.")
    if not highlights:
        highlights.append("The main risks are usually the clauses that control termination, liability, intellectual property, and renewal.")

    history_note = ""
    if conversation_history:
        history_note = f" I can also see {len(conversation_history)} prior chat message(s) in this session."

    return (
        f"Based on the contract context, the biggest risks are: {' '.join(highlights)}"
        f" For your question, '{user_message}', I would focus on whether the clause is one-sided, how long it lasts, and whether you can negotiate narrower language."
        f" Note: This is AI analysis, not legal advice. Consult a licensed attorney for legal decisions.{history_note}"
    )


def _fallback_compare(text_a: str, text_b: str) -> dict:
    a_lower = text_a.lower()
    b_lower = text_b.lower()
    keywords = ["non-compete", "indemn", "arbitr", "liabil", "confidential", "renew", "data", "ip", "termination"]
    differences = []
    favorable_count = 0
    unfavorable_count = 0

    for keyword in keywords:
        in_a = keyword in a_lower
        in_b = keyword in b_lower
        if in_a == in_b:
            continue
        verdict = "unfavorable" if in_b and not in_a else "favorable"
        if verdict == "favorable":
            favorable_count += 1
        else:
            unfavorable_count += 1
        differences.append(
            {
                "clause_name": keyword.title(),
                "original_text": text_a[:200],
                "modified_text": text_b[:200],
                "verdict": verdict,
                "explanation": "The second contract is more restrictive in this area." if verdict == "unfavorable" else "The second contract is less restrictive in this area.",
                "winner": "Contract B" if verdict == "unfavorable" else "Contract A",
                "category": keyword.title(),
                "contract_a_text": text_a[:200],
                "contract_b_text": text_b[:200],
            }
        )

    overall_risk = "HIGH" if unfavorable_count >= 3 else "MEDIUM" if unfavorable_count else "LOW"
    return {
        "summary": "Fallback comparison based on key contract language differences.",
        "overall_risk": overall_risk,
        "recommendation": "Contract A" if favorable_count >= unfavorable_count else "Contract B",
        "clauses_altered": len(differences),
        "favorable_count": favorable_count,
        "unfavorable_count": unfavorable_count,
        "differences": differences,
    }


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

    if _model is None:
        return _fallback_analysis(document_text)

    try:
        raw = _call_gemini(prompt)
        result = _extract_json(raw)
    except Exception as exc:
        logger.warning("Gemini analysis unavailable; using local fallback: %s", exc)
        return _fallback_analysis(document_text)

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

    if _model is None:
        return [
            {
                "clause_title": c.get("title") or c.get("clause_title") or "Clause",
                "risk_level": c.get("risk_level", "HIGH"),
                "current_language": (c.get("clause_text") or c.get("original_text", ""))[:150],
                "suggested_alternative": c.get("recommendation", "Narrow the clause and add mutual protections."),
                "what_to_ask": c.get("recommendation", "Ask for narrower language and mutual limits."),
                "negotiation_tip": "Use specific business impact to justify the change.",
                "priority": "high" if c.get("risk_level") == "CRITICAL" else "medium",
            }
            for c in risky
        ]

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

    try:
        raw = _call_gemini(prompt)
        return _extract_json(raw)
    except Exception as exc:
        logger.warning("Negotiation recommendations fallback used: %s", exc)
        return [
            {
                "clause_title": c.get("title") or c.get("clause_title") or "Clause",
                "risk_level": c.get("risk_level", "HIGH"),
                "current_language": (c.get("clause_text") or c.get("original_text", ""))[:150],
                "suggested_alternative": c.get("recommendation", "Narrow the clause and add mutual protections."),
                "what_to_ask": c.get("recommendation", "Ask for narrower language and mutual limits."),
                "negotiation_tip": "Use specific business impact to justify the change.",
                "priority": "high" if c.get("risk_level") == "CRITICAL" else "medium",
            }
            for c in risky
        ]


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

    if _model is None:
        return _fallback_chat(document_text, clauses_summary, conversation_history, user_message)

    try:
        return _call_gemini(prompt)
    except Exception as exc:
        logger.warning("Chat fallback used: %s", exc)
        return _fallback_chat(document_text, clauses_summary, conversation_history, user_message)


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

    if _model is None:
        return _fallback_compare(text_a, text_b)

    try:
        raw = _call_gemini(prompt)
        result = _extract_json(raw)
    except Exception as exc:
        logger.warning("Comparison fallback used: %s", exc)
        return _fallback_compare(text_a, text_b)
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

    if _model is None:
        return _fallback_glossary(term)

    try:
        raw = _call_gemini(prompt)
        result = _extract_json(raw)
    except Exception as exc:
        logger.warning("Glossary fallback used: %s", exc)
        return _fallback_glossary(term)
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
