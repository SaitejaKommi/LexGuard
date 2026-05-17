"""test_risk_scorer.py - Tests for risk scoring logic."""
import pytest
from backend.services.risk_scorer import (
    score_to_level, level_to_score, build_risk_distribution,
    compute_weighted_risk_score, get_risk_color, filter_clauses_by_risk
)


def test_score_to_level_critical():
    assert score_to_level(85) == "CRITICAL"


def test_score_to_level_high():
    assert score_to_level(70) == "HIGH"


def test_score_to_level_medium():
    assert score_to_level(50) == "MEDIUM"


def test_score_to_level_low():
    assert score_to_level(25) == "LOW"


def test_score_to_level_safe():
    assert score_to_level(10) == "SAFE"


def test_level_to_score_critical():
    assert level_to_score("CRITICAL") == 80


def test_build_distribution():
    clauses = [
        {"risk_level": "CRITICAL"},
        {"risk_level": "HIGH"},
        {"risk_level": "HIGH"},
        {"risk_level": "SAFE"},
    ]
    dist = build_risk_distribution(clauses)
    assert dist["CRITICAL"] == 1
    assert dist["HIGH"] == 2
    assert dist["SAFE"] == 1


def test_compute_weighted_score_empty():
    assert compute_weighted_risk_score([]) == 0


def test_compute_weighted_score_all_safe():
    clauses = [{"risk_level": "SAFE", "risk_score": 0}] * 5
    assert compute_weighted_risk_score(clauses) == 0


def test_get_risk_color_critical():
    assert get_risk_color("CRITICAL") == "#ff3b3b"


def test_filter_clauses_by_risk():
    clauses = [
        {"risk_level": "SAFE"}, {"risk_level": "LOW"},
        {"risk_level": "HIGH"}, {"risk_level": "CRITICAL"},
    ]
    result = filter_clauses_by_risk(clauses, min_level="HIGH")
    levels = [c["risk_level"] for c in result]
    assert "SAFE" not in levels
    assert "HIGH" in levels
    assert "CRITICAL" in levels
