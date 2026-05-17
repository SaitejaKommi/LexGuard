"""test_analyze.py - Tests for /api/analyze route."""
import io
import pytest


def test_analyze_missing_file(client):
    resp = client.post("/api/analyze")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "code" in data


def test_analyze_invalid_extension(client):
    data = {"file": (io.BytesIO(b"content"), "malware.exe")}
    resp = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_analyze_empty_file(client):
    data = {"file": (io.BytesIO(b""), "empty.txt")}
    resp = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert resp.status_code in (400, 422)


def test_analyze_txt_without_gemini(client, mocker):
    mocker.patch(
        "backend.services.clause_extractor.run_full_extraction_pipeline",
        side_effect=RuntimeError("Gemini not configured"),
    )
    file_data = b"This is a test contract text."
    data = {"file": (io.BytesIO(file_data), "test.txt")}
    resp = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert resp.status_code in (502, 200)


def test_analyze_txt_mocked_success(client, mocker):
    mocker.patch(
        "backend.services.clause_extractor.run_full_extraction_pipeline",
        return_value={
            "clauses": [{"clause_text": "Test", "risk_level": "LOW", "risk_score": 20}],
            "overall_risk_score": 20,
            "risk_distribution": {"LOW": 1},
            "negotiation_recommendations": [],
            "summary": "Low risk contract.",
        },
    )
    mocker.patch("backend.services.mongodb_service.save_analysis", return_value="abc123")
    mocker.patch("backend.services.mongodb_service.get_analysis_by_hash", return_value=None)
    mocker.patch("backend.services.mongodb_service.upsert_user", return_value=None)
    mocker.patch("backend.services.mongodb_service.compute_doc_hash", return_value="hash123")
    mocker.patch("backend.services.firebase_service.backup_analysis_to_firestore", return_value=True)

    data = {"file": (io.BytesIO(b"Employment contract text here."), "contract.txt")}
    resp = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    result = resp.get_json()
    assert "overall_risk_score" in result
    assert "clauses" in result
