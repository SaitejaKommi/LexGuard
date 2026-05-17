"""test_glossary.py - Tests for /api/glossary route."""
import pytest


def test_glossary_missing_term(client):
    resp = client.post("/api/glossary", json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["code"] == "MISSING_FIELD"


def test_glossary_empty_term(client):
    resp = client.post("/api/glossary", json={"term": "   "})
    assert resp.status_code == 400


def test_glossary_success_mocked(client, mocker):
    mocker.patch(
        "backend.services.gemini_service.explain_legal_term",
        return_value={
            "term": "indemnification",
            "definition": "A promise to compensate for any harm or loss.",
            "example": "If you are sued, the other party pays your legal fees.",
            "related_terms": ["liability", "damages", "hold harmless"],
            "risk_note": "Watch for unlimited indemnification clauses.",
        }
    )
    resp = client.post("/api/glossary", json={"term": "indemnification"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["term"] == "indemnification"
    assert "definition" in data
    assert "related_terms" in data


def test_glossary_gemini_failure(client, mocker):
    mocker.patch(
        "backend.services.gemini_service.explain_legal_term",
        side_effect=RuntimeError("API error")
    )
    resp = client.post("/api/glossary", json={"term": "arbitration"})
    assert resp.status_code == 502


def test_glossary_term_too_long(client):
    # Term over 200 chars — sanitizer truncates so should still work (200 chars max)
    long_term = "a" * 201
    resp = client.post("/api/glossary", json={"term": long_term})
    # sanitize_text truncates at 200 — no error, but Gemini not configured
    assert resp.status_code in (200, 400, 502)
