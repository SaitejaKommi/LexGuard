"""
config.py - Centralised configuration loader for LexGuard.

All environment variables are read here and exposed as typed attributes on the
``Config`` dataclass.  No other module in the application should call
``os.environ`` directly.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))


@dataclass
class Config:
    """Application configuration resolved from environment variables.

    All sensitive credentials are read from the process environment so they
    are never committed to source control.
    """

    # ------------------------------------------------------------------
    # Flask core
    # ------------------------------------------------------------------
    SECRET_KEY: str = field(
        default_factory=lambda: os.environ.get(
            "SECRET_KEY", os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")
        )
    )
    FLASK_SECRET_KEY: str = field(
        default_factory=lambda: os.environ.get(
            "FLASK_SECRET_KEY", os.environ.get("SECRET_KEY", "change-me-in-production")
        )
    )
    DEBUG: bool = field(
        default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true"
    )
    TESTING: bool = field(
        default_factory=lambda: os.environ.get("TESTING", "false").lower() == "true"
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: list = field(
        default_factory=lambda: [
            o.strip()
            for o in os.environ.get(
                "CORS_ORIGINS",
                "http://localhost:3000,http://localhost:5500,http://localhost:5501,"
                "http://localhost:5505,http://127.0.0.1:5500,http://127.0.0.1:5501,"
                "http://127.0.0.1:5505,null",
            ).split(",")
            if o.strip()
        ]
    )

    # ------------------------------------------------------------------
    # MongoDB
    # ------------------------------------------------------------------
    MONGO_URI: str = field(
        default_factory=lambda: os.environ.get("MONGO_URI", os.environ.get("MONGODB_URI", ""))
    )
    MONGODB_URI: str = field(
        default_factory=lambda: os.environ.get("MONGODB_URI", os.environ.get("MONGO_URI", ""))
    )
    MONGO_DB_NAME: str = field(
        default_factory=lambda: os.environ.get("MONGO_DB_NAME", "lexguard")
    )

    # ------------------------------------------------------------------
    # Google Gemini
    # ------------------------------------------------------------------
    GEMINI_API_KEY: str = field(
        default_factory=lambda: os.environ.get("GEMINI_API_KEY", "")
    )

    # ------------------------------------------------------------------
    # Optional News API
    # ------------------------------------------------------------------
    NEWS_API_KEY: str = field(
        default_factory=lambda: os.environ.get("NEWS_API_KEY", "")
    )

    # ------------------------------------------------------------------
    # Google Cloud Translate
    # ------------------------------------------------------------------
    GOOGLE_TRANSLATE_API_KEY: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
    )

    # ------------------------------------------------------------------
    # Google Cloud Text-to-Speech
    # ------------------------------------------------------------------
    GOOGLE_TTS_API_KEY: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_TTS_API_KEY", "")
    )
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = field(
        default_factory=lambda: os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    )

    # ------------------------------------------------------------------
    # Google Custom Search
    # ------------------------------------------------------------------
    GOOGLE_SEARCH_API_KEY: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_SEARCH_API_KEY", "")
    )
    GOOGLE_SEARCH_ENGINE_ID: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_SEARCH_ENGINE_ID", "")
    )

    # ------------------------------------------------------------------
    # Google Analytics 4
    # ------------------------------------------------------------------
    GA4_MEASUREMENT_ID: str = field(
        default_factory=lambda: os.environ.get("GA4_MEASUREMENT_ID", "G-XXXXXXXXXX")
    )

    # ------------------------------------------------------------------
    # Firebase
    # ------------------------------------------------------------------
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = field(
        default_factory=lambda: os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    )
    FIREBASE_PROJECT_ID: str = field(
        default_factory=lambda: os.environ.get("FIREBASE_PROJECT_ID", "")
    )

    # ------------------------------------------------------------------
    # Tesseract OCR
    # ------------------------------------------------------------------
    TESSERACT_CMD: Optional[str] = field(
        default_factory=lambda: os.environ.get("TESSERACT_CMD")
    )

    # ------------------------------------------------------------------
    # MyMemory fallback
    # ------------------------------------------------------------------
    MYMEMORY_EMAIL: str = field(
        default_factory=lambda: os.environ.get("MYMEMORY_EMAIL", "")
    )


def get_config() -> Config:
    """Instantiate and return the application configuration singleton.

    Returns:
        Populated :class:`Config` instance.
    """
    return Config()
