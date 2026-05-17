"""
clause_extractor.py - Orchestrates clause extraction and enrichment pipeline.

Uses Gemini single-pass analysis for efficiency, then enriches with RAG
similarity scores from the embedding service.
"""

import logging

from . import gemini_service, embedding_service, risk_scorer

logger = logging.getLogger(__name__)


def run_full_extraction_pipeline(document_text: str) -> dict:
    """Execute the complete clause analysis pipeline on a document.

    Pipeline stages:
        1. Single-pass Gemini analysis (clauses + risk + summary in one call)
        2. Compute RAG similarity scores (if embedder available)
        3. Compute overall risk score and distribution
        4. Generate negotiation recommendations

    Args:
        document_text: Full extracted text of the contract.

    Returns:
        Dict with keys:
            - clauses: enriched clause list
            - overall_risk_score: int 0-100
            - risk_distribution: dict of level -> count
            - negotiation_recommendations: list of recommendation dicts
            - summary: analysis summary string
            - contract_type: detected contract type
            - red_flags: list of top risk flags

    Raises:
        RuntimeError: If Gemini API calls fail critically.
    """
    logger.info("Starting single-pass clause extraction pipeline.")

    # Step 1: Single-pass Gemini analysis
    analysis = gemini_service.analyze_contract_full(document_text)
    clauses = analysis.get("clauses", [])
    logger.info("Single-pass analysis extracted %d clauses.", len(clauses))

    # Step 2: Enrich with RAG similarity (if embedder available)
    # Map 'original_text' to 'clause_text' for embedding compatibility
    for clause in clauses:
        if "clause_text" not in clause and "original_text" in clause:
            clause["clause_text"] = clause["original_text"]

    try:
        clauses = embedding_service.compute_clause_similarities(clauses)
        logger.info("Similarity scoring complete.")
    except Exception as exc:
        logger.warning("Embedding similarity failed (non-critical): %s", exc)
        for clause in clauses:
            clause.setdefault("similarity_score", 0.5)
            clause.setdefault("deviation_percent", None)
            clause.setdefault("matched_standard", None)
            clause.setdefault("similarity_flag", False)

    # Step 3: Compute overall risk score and distribution
    overall_score = analysis.get("overall_score") or risk_scorer.compute_weighted_risk_score(clauses)
    distribution = risk_scorer.build_risk_distribution(clauses)

    # Step 4: Generate negotiation recommendations
    try:
        recommendations = gemini_service.generate_negotiation_recommendations(clauses)
        logger.info("Negotiation recommendations: %d generated.", len(recommendations))
    except Exception as exc:
        logger.warning("Negotiation recommendations failed (non-critical): %s", exc)
        recommendations = []

    summary = analysis.get("summary", f"Contract analyzed with overall risk score of {overall_score}/100.")

    return {
        "clauses": clauses,
        "overall_risk_score": overall_score,
        "risk_distribution": distribution,
        "negotiation_recommendations": recommendations,
        "summary": summary,
        "contract_type": analysis.get("contract_type", "Legal Agreement"),
        "red_flags": analysis.get("red_flags", []),
        "negotiation_priorities": analysis.get("negotiation_priorities", []),
    }
