"""test_compare.py - Tests for /api/compare route."""
import io
import pytest


def test_compare_missing_both_files(client):
    resp = client.post("/api/compare")
    assert resp.status_code == 400


def test_compare_missing_file_b(client):
    data = {"file_a": (io.BytesIO(b"Contract A text."), "a.txt")}
    resp = client.post("/api/compare", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_compare_invalid_extension(client):
    data = {
        "file_a": (io.BytesIO(b"Contract A"), "a.exe"),
        "file_b": (io.BytesIO(b"Contract B"), "b.txt"),
    }
    resp = client.post("/api/compare", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_compare_gemini_failure(client, mocker):
    mocker.patch("backend.services.gemini_service.compare_contracts",
                 side_effect=RuntimeError("Gemini error"))
    data = {
        "file_a": (io.BytesIO(b"Contract A text here."), "a.txt"),
        "file_b": (io.BytesIO(b"Contract B text here."), "b.txt"),
    }
    resp = client.post("/api/compare", data=data, content_type="multipart/form-data")
    assert resp.status_code == 502


def test_compare_success_mocked(client, mocker):
    mocker.patch("backend.services.gemini_service.compare_contracts",
                 return_value={"summary": "A is better", "recommendation": "Contract A",
                               "differences": []})
    data = {
        "file_a": (io.BytesIO(b"Contract A with good terms."), "a.txt"),
        "file_b": (io.BytesIO(b"Contract B with bad terms."), "b.txt"),
    }
    resp = client.post("/api/compare", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    result = resp.get_json()
    assert "comparison" in result
