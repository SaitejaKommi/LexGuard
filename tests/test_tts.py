"""test_tts.py - Tests for /api/tts route."""
import pytest


def test_tts_empty_text(client):
    resp = client.post("/api/tts", json={"text": "   ", "language_code": "en-US"})
    assert resp.status_code == 400


def test_tts_no_google_key_returns_fallback(client):
    """Without a Google TTS key the endpoint must return web_speech_api fallback."""
    resp = client.post("/api/tts", json={"text": "Hello legal world", "language_code": "en-US"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["source"] == "web_speech_api"
    assert data["audio_base64"] is None
    assert data["fallback_text"] == "Hello legal world"


def test_tts_google_success_mocked(client, mocker):
    mocker.patch(
        "backend.services.tts_service.synthesize_speech",
        return_value={
            "audio_base64": "AAAA",
            "source": "google",
            "success": True,
            "fallback_text": "Hello",
        }
    )
    resp = client.post("/api/tts", json={"text": "Hello", "language_code": "en-US"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["source"] == "google"
    assert data["audio_base64"] == "AAAA"


def test_tts_invalid_language_code(client):
    resp = client.post("/api/tts", json={"text": "Hello", "language_code": "123!!"})
    assert resp.status_code == 400


def test_tts_default_language(client):
    """Omitting language_code should use the default en-US."""
    resp = client.post("/api/tts", json={"text": "Hello world contract"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fallback_text" in data
