"""
clause_extractor.py - Orchestrates clause extraction and enrichment pipeline.

Combines Gemini clause extraction, risk scoring, RAG similarity, and
negotiation recommendation generation into a single callable pipeline.
"""

import logging

from . import gemini_service, embedding_service, risk_scorer

logger = logging.getLogger(__name__)


def run_full_extraction_pipeline(document_text: str) -> dict:
    """Execute the complete clause analysis pipeline on a document.

    Pipeline stages:
        1. Extract clauses with Gemini
        2. Score risk levels with Gemini
        3. Compute RAG similarity scores
        4. Generate negotiation recommendations
        5. Compute overall risk score and distribution

    Args:
        document_text: Full extracted text of the contract.

    Returns:
        Dict with keys:
            - clauses: enriched clause list
            - overall_risk_score: int 0-100
            - risk_distribution: dict of level → count
            - negotiation_recommendations: list of recommendation dicts
            - summary: analysis summary string

    Raises:
        RuntimeError: If Gemini API calls fail critically.
    """
    logger.info("Starting clause extraction pipeline.")

    clauses = gemini_service.extract_clauses(document_text)
    logger.info("Extracted %d clauses.", len(clauses))

    clauses = gemini_service.score_risks(clauses)
    logger.info("Risk scoring complete.")

    clauses = embedding_service.compute_clause_similarities(clauses)
    logger.info("Similarity scoring complete.")

    recommendations = gemini_service.generate_negotiation_recommendations(clauses)
    logger.info("Negotiation recommendations: %d generated.", len(recommendations))

    overall_score = risk_scorer.compute_weighted_risk_score(clauses)
    distribution = risk_scorer.build_risk_distribution(clauses)
    summary = gemini_service.generate_analysis_summary(document_text, overall_score, clauses)

    return {
        "clauses": clauses,
        "overall_risk_score": overall_score,
        "risk_distribution": distribution,
        "negotiation_recommendations": recommendations,
        "summary": summary,
    }
