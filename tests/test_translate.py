"""test_translate.py - Tests for /api/translate route."""
import pytest


def test_translate_empty_text(client):
    resp = client.post("/api/translate", json={"text": "   ", "target_lang": "hi"})
    assert resp.status_code == 400


def test_translate_invalid_lang(client):
    resp = client.post("/api/translate", json={"text": "Hello", "target_lang": "xyz123"})
    assert resp.status_code in (400,)


def test_translate_english_passthrough(client):
    resp = client.post("/api/translate", json={"text": "Hello contract world", "target_lang": "en"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["translated_text"] == "Hello contract world"
    assert data["source"] == "passthrough"


def test_translate_to_hindi_mocked(client, mocker):
    mocker.patch(
        "backend.services.translate_service.translate_text",
        return_value={"translated_text": "नमस्ते", "source": "mymemory", "success": True}
    )
    resp = client.post("/api/translate", json={"text": "Hello", "target_lang": "hi"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


def test_translate_missing_body(client):
    resp = client.post("/api/translate", json={})
    # empty text raises ValueError
    assert resp.status_code == 400
