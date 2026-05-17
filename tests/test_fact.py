"""test_fact.py - Tests for /api/fact and /api/fact/categories routes."""
import pytest
import time


def test_fact_categories_returns_list(client):
    resp = client.get("/api/fact/categories")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "categories" in data
    assert len(data["categories"]) > 0
    assert "Contract Law" in data["categories"]


def test_fact_with_valid_category_mocked(client, mocker):
    mocker.patch(
        "backend.routes.fact._generate_fact",
        return_value={
            "fact": "You can negotiate any clause in a standard employment contract.",
            "what_to_do": "Ask your employer to revise the non-compete clause scope.",
            "category": "Contract Law",
        }
    )
    resp = client.get("/api/fact?category=Contract+Law")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fact" in data
    assert data["category"] == "Contract Law"
    assert data["cached"] is False


def test_fact_default_category(client, mocker):
    mocker.patch(
        "backend.routes.fact._generate_fact",
        return_value={
            "fact": "A legal insight for today.",
            "what_to_do": "Review your contract.",
            "category": "Employment Law",
        }
    )
    resp = client.get("/api/fact")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fact" in data
    assert "category" in data


def test_fact_cache_hit(client, mocker):
    """Second request with same category should return cached=True."""
    import backend.routes.fact as fact_module

    # Pre-populate the cache
    fact_module._fact_cache["Contract Law"] = {
        "fact": "Cached legal insight.",
        "what_to_do": "Review carefully.",
        "category": "Contract Law",
        "timestamp": time.time(),  # Fresh timestamp
    }

    resp = client.get("/api/fact?category=Contract+Law")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["cached"] is True
    assert data["fact"] == "Cached legal insight."

    # Cleanup
    del fact_module._fact_cache["Contract Law"]


def test_fact_gemini_failure_returns_static_fallback(client, mocker):
    """When Gemini fails, /api/fact must return the static fallback, not 500."""
    import backend.routes.fact as fact_module
    # Ensure cache is empty for this category
    fact_module._fact_cache.pop("Non-Compete Law", None)

    mocker.patch(
        "backend.routes.fact._generate_fact",
        side_effect=RuntimeError("Gemini offline")
    )
    resp = client.get("/api/fact?category=Non-Compete+Law")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fact" in data
    assert data.get("source") == "static_fallback"


def test_fact_invalid_category_uses_default(client, mocker):
    mocker.patch(
        "backend.routes.fact._generate_fact",
        return_value={
            "fact": "A general legal fact.",
            "what_to_do": "Consult a lawyer.",
            "category": "Contract Law",
        }
    )
    resp = client.get("/api/fact?category=InvalidCategory")
    assert resp.status_code == 200
