"""test_health.py - Tests for /api/health endpoint."""
import pytest


def test_health_returns_200(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_health_has_status_key(client):
    data = client.get("/api/health").get_json()
    assert "status" in data


def test_health_has_version(client):
    data = client.get("/api/health").get_json()
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_health_has_services_dict(client):
    data = client.get("/api/health").get_json()
    assert "services" in data
    assert isinstance(data["services"], dict)


def test_health_services_contain_expected_keys(client):
    data = client.get("/api/health").get_json()
    for key in ("mongodb", "gemini", "embedding", "firebase"):
        assert key in data["services"]
