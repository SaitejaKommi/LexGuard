"""test_gemini_service.py - Unit tests for gemini_service (mocked at SDK level)."""
import pytest
import json
from unittest.mock import MagicMock, patch


def test_extract_json_plain():
    from backend.services.gemini_service import _extract_json
    data = _extract_json('{"key": "value"}')
    assert data == {"key": "value"}


def test_extract_json_with_fences():
    from backend.services.gemini_service import _extract_json
    raw = '```json\n{"overall_score": 75}\n```'
    data = _extract_json(raw)
    assert data["overall_score"] == 75


def test_extract_json_array():
    from backend.services.gemini_service import _extract_json
    raw = '[{"risk_level": "HIGH"}, {"risk_level": "LOW"}]'
    data = _extract_json(raw)
    assert len(data) == 2


def test_extract_json_invalid_raises():
    from backend.services.gemini_service import _extract_json
    with pytest.raises(ValueError):
        _extract_json("this is not json at all!!!")


def test_compute_overall_risk_score_empty():
    from backend.services.gemini_service import compute_overall_risk_score
    assert compute_overall_risk_score([]) == 0


def test_compute_overall_risk_score_all_safe():
    from backend.services.gemini_service import compute_overall_risk_score
    clauses = [{"risk_level": "SAFE", "risk_score": 0}] * 5
    assert compute_overall_risk_score(clauses) == 0


def test_compute_overall_risk_score_critical():
    from backend.services.gemini_service import compute_overall_risk_score
    clauses = [{"risk_level": "CRITICAL", "risk_score": 90}]
    score = compute_overall_risk_score(clauses)
    assert score > 70


def test_get_model_raises_when_not_init():
    from backend.services import gemini_service
    original = gemini_service._model
    gemini_service._model = None
    with pytest.raises(RuntimeError, match="not initialised"):
        gemini_service._get_model()
    gemini_service._model = original


def test_generate_analysis_summary_fallback(mocker):
    from backend.services import gemini_service
    mocker.patch.object(gemini_service, "_call_gemini", side_effect=RuntimeError("fail"))
    gemini_service._model = MagicMock()  # make model appear initialized
    result = gemini_service.generate_analysis_summary("contract text", 75, [])
    assert "75" in result
    gemini_service._model = None


def test_analyze_contract_full_normalizes_missing_fields(mocker):
    from backend.services import gemini_service
    gemini_service._model = MagicMock()
    mocker.patch.object(gemini_service, "_call_gemini", return_value=json.dumps({
        "overall_score": 60,
        "risk_level": "HIGH",
        "clauses": [
            {"id": "c1", "title": "Non-compete", "risk_level": "HIGH", "risk_score": 70}
        ]
    }))
    result = gemini_service.analyze_contract_full("test contract text")
    assert result["overall_score"] == 60
    assert result["clauses"][0]["plain_english"] == "No explanation available."
    assert result["clauses"][0]["recommendation"] == "Seek legal advice."
    gemini_service._model = None


def test_explain_legal_term_normalizes(mocker):
    from backend.services import gemini_service
    gemini_service._model = MagicMock()
    mocker.patch.object(gemini_service, "_call_gemini", return_value=json.dumps({
        "term": "arbitration",
        "definition": "A private dispute resolution process.",
    }))
    result = gemini_service.explain_legal_term("arbitration")
    assert result["term"] == "arbitration"
    assert "related_terms" in result  # defaulted
    gemini_service._model = None


def test_negotiate_recommendations_returns_empty_if_no_risky(mocker):
    from backend.services.gemini_service import generate_negotiation_recommendations
    result = generate_negotiation_recommendations([{"risk_level": "SAFE"}])
    assert result == []
