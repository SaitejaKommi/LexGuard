"""test_chat.py - Tests for /api/chat route."""
import pytest


def test_chat_without_document(client):
    resp = client.post("/api/chat", json={"message": "What is the risk?"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["code"] == "SESSION_NOT_FOUND"


def test_chat_empty_message(client):
    with client.session_transaction() as sess:
        sess["current_doc_text"] = "Contract text"
        sess["current_clauses_summary"] = "[]"
    resp = client.post("/api/chat", json={"message": "   "})
    assert resp.status_code == 400


def test_chat_message_too_long(client):
    with client.session_transaction() as sess:
        sess["current_doc_text"] = "Contract text"
    resp = client.post("/api/chat", json={"message": "x" * 2000})
    assert resp.status_code == 400


def test_chat_success_mocked(client, mocker):
    with client.session_transaction() as sess:
        sess["current_doc_text"] = "This is a test employment contract."
        sess["current_clauses_summary"] = "[]"
        sess["session_id"] = "test-session-123"

    mocker.patch("backend.services.gemini_service.chat_with_document",
                 return_value="This clause limits your rights.")
    mocker.patch("backend.services.mongodb_service.get_chat_history", return_value=[])
    mocker.patch("backend.services.mongodb_service.save_chat_message", return_value=None)

    resp = client.post("/api/chat", json={"message": "Is this contract risky?"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "response" in data


def test_chat_gemini_failure(client, mocker):
    with client.session_transaction() as sess:
        sess["current_doc_text"] = "Contract text here."
        sess["current_clauses_summary"] = "[]"

    mocker.patch("backend.services.gemini_service.chat_with_document",
                 side_effect=RuntimeError("API Error"))
    mocker.patch("backend.services.mongodb_service.get_chat_history", return_value=[])

    resp = client.post("/api/chat", json={"message": "What does section 3 mean?"})
    assert resp.status_code == 502
