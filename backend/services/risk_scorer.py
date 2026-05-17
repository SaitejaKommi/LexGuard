"""
risk_scorer.py - Risk scoring aggregation and helpers for LexGuard.

Provides helper functions for computing per-clause and overall risk metrics
independent of the Gemini service (can be used in tests without API calls).
"""

from ..utils.constants import (
    RISK_SCORE_CRITICAL_MIN,
    RISK_SCORE_HIGH_MIN,
    RISK_SCORE_MEDIUM_MIN,
    RISK_SCORE_LOW_MIN,
    RISK_LEVEL_WEIGHTS,
)


def score_to_level(score: int) -> str:
    """Map a numeric risk score to a named risk level.

    Args:
        score: Integer risk score in range 0–100.

    Returns:
        Risk level string: CRITICAL, HIGH, MEDIUM, LOW, or SAFE.
    """
    if score >= RISK_SCORE_CRITICAL_MIN:
        return "CRITICAL"
    if score >= RISK_SCORE_HIGH_MIN:
        return "HIGH"
    if score >= RISK_SCORE_MEDIUM_MIN:
        return "MEDIUM"
    if score >= RISK_SCORE_LOW_MIN:
        return "LOW"
    return "SAFE"


def level_to_score(level: str) -> int:
    """Return the minimum threshold score for a given risk level.

    Args:
        level: Risk level string (CRITICAL / HIGH / MEDIUM / LOW / SAFE).

    Returns:
        Minimum integer score for that level.
    """
    thresholds = {
        "CRITICAL": RISK_SCORE_CRITICAL_MIN,
        "HIGH": RISK_SCORE_HIGH_MIN,
        "MEDIUM": RISK_SCORE_MEDIUM_MIN,
        "LOW": RISK_SCORE_LOW_MIN,
        "SAFE": 0,
    }
    return thresholds.get(level.upper(), 0)


def build_risk_distribution(clauses: list[dict]) -> dict[str, int]:
    """Count clauses per risk level for chart rendering.

    Args:
        clauses: List of scored clause dicts with 'risk_level' keys.

    Returns:
        Dictionary mapping risk level names to counts.
    """
    distribution: dict[str, int] = {
        "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "SAFE": 0,
    }
    for clause in clauses:
        level = clause.get("risk_level", "SAFE").upper()
        if level in distribution:
            distribution[level] += 1
        else:
            distribution["SAFE"] += 1
    return distribution


def compute_weighted_risk_score(clauses: list[dict]) -> int:
    """Compute a weighted overall risk score from a list of scored clauses.

    Weights higher-risk clauses more heavily so a single CRITICAL clause
    can significantly raise the overall score.

    Args:
        clauses: List of scored clause dicts.

    Returns:
        Integer overall risk score 0–100.
    """
    if not clauses:
        return 0

    level_weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "SAFE": 0}
    total_weight = 0
    weighted_sum = 0.0

    for clause in clauses:
        level = clause.get("risk_level", "SAFE").upper()
        score = clause.get("risk_score", 0)
        weight = level_weights.get(level, 0) + 1
        total_weight += weight
        weighted_sum += score * weight

    if total_weight == 0:
        return 0
    return min(100, int(weighted_sum / total_weight))


def get_risk_color(level: str) -> str:
    """Return the hex color associated with a risk level.

    Args:
        level: Risk level string.

    Returns:
        Hex color string.
    """
    colors = {
        "CRITICAL": "#ff3b3b",
        "HIGH": "#ff8c00",
        "MEDIUM": "#ffd700",
        "LOW": "#00d4ff",
        "SAFE": "#00e676",
    }
    return colors.get(level.upper(), "#888888")


def filter_clauses_by_risk(clauses: list[dict], min_level: str = "LOW") -> list[dict]:
    """Return only clauses at or above the specified minimum risk level.

    Args:
        clauses: Full clause list.
        min_level: Minimum risk level to include.

    Returns:
        Filtered clause list.
    """
    order = ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    min_idx = order.index(min_level.upper()) if min_level.upper() in order else 0
    return [
        c for c in clauses
        if order.index(c.get("risk_level", "SAFE").upper()) >= min_idx
    ]
