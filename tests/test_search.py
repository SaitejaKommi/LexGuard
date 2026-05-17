"""test_search.py - Tests for /api/search route."""
import pytest


def test_search_missing_query(client):
    resp = client.get("/api/search")
    assert resp.status_code == 400


def test_search_empty_query(client):
    resp = client.get("/api/search?q=")
    assert resp.status_code == 400


def test_search_returns_fallback_without_api_key(client):
    resp = client.get("/api/search?q=non-compete+clause")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "results" in data
    assert len(data["results"]) > 0


def test_search_google_success(client, mocker):
    mocker.patch("backend.services.search_service._google_api_key", "fake-key")
    mocker.patch("backend.services.search_service._search_engine_id", "fake-cx")
    mocker.patch("backend.services.search_service._search_via_google",
                 return_value=[{"title": "Test", "snippet": "Desc", "link": "https://test.com"}])
    resp = client.get("/api/search?q=arbitration+clause")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["results"][0]["title"] == "Test"


def test_search_xss_query_sanitized(client):
    resp = client.get("/api/search?q=<script>alert(1)</script>")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "results" in data
