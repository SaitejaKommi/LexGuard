"""test_history.py - Tests for /api/history route."""
import pytest


def test_history_no_email_returns_empty(client):
    """No email returns 200 with empty history."""
    resp = client.get("/api/history")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["history"] == []
    assert data["count"] == 0


def test_history_invalid_email(client):
    resp = client.get("/api/history?email=not-an-email")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["code"] == "INVALID_INPUT"


def test_history_with_valid_email_no_mongo(client):
    """Valid email but MongoDB not connected — returns 200 with empty array."""
    resp = client.get("/api/history?email=test@example.com")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "history" in data


def test_history_by_id_not_found(client):
    resp = client.get("/api/history/507f1f77bcf86cd799439011")
    assert resp.status_code in (404, 500)


def test_history_by_id_invalid_id(client):
    resp = client.get("/api/history/invalid-id")
    assert resp.status_code in (404, 500)
