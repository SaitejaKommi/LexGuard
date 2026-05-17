"""
conftest.py - Shared pytest fixtures for LexGuard test suite.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from backend.app import create_app
from backend.config import Config


@pytest.fixture
def test_config():
    cfg = Config()
    cfg.TESTING = True
    cfg.SECRET_KEY = "test-secret"
    cfg.GEMINI_API_KEY = ""
    cfg.MONGO_URI = ""
    cfg.CORS_ORIGINS = ["*"]
    return cfg


@pytest.fixture
def app(test_config):
    application = create_app(test_config)
    application.config["TESTING"] = True
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_txt_bytes():
    return b"This is a sample employment contract for testing purposes."


@pytest.fixture
def sample_pdf_bytes():
    # Minimal valid PDF header
    return b"%PDF-1.4 1 0 obj << /Type /Catalog >> endobj"
