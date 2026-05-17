"""test_negotiate.py - Tests for /api/negotiate route."""
import pytest


def test_negotiate_missing_clauses(client):
    resp = client.post("/api/negotiate", json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["code"] == "MISSING_FIELD"


def test_negotiate_empty_clauses(client):
    resp = client.post("/api/negotiate", json={"clauses": []})
    assert resp.status_code == 400


def test_negotiate_no_risky_clauses(client):
    resp = client.post("/api/negotiate", json={"clauses": [{"risk_level": "SAFE", "title": "intro"}]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["recommendations"] == []


def test_negotiate_risky_clauses_mocked(client, mocker):
    mocker.patch(
        "backend.services.gemini_service.generate_negotiation_recommendations",
        return_value=[{"clause_title": "Non-compete", "priority": "high", "suggested_alternative": "Remove."}]
    )
    clauses = [{"risk_level": "CRITICAL", "title": "Non-compete", "original_text": "No work allowed."}]
    resp = client.post("/api/negotiate", json={"clauses": clauses})
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["recommendations"]) == 1


def test_negotiate_gemini_failure(client, mocker):
    mocker.patch(
        "backend.services.gemini_service.generate_negotiation_recommendations",
        side_effect=RuntimeError("Gemini error")
    )
    clauses = [{"risk_level": "HIGH", "title": "Arbitration", "original_text": "Binding arbitration."}]
    resp = client.post("/api/negotiate", json={"clauses": clauses})
    assert resp.status_code == 502
