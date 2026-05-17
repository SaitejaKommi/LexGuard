"""
app.py - Flask application factory for LexGuard.

Creates and configures the Flask app, registers all blueprints,
initialises all services, and attaches security headers to every response.
"""

import logging
from typing import Optional

from flask import Flask, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import Config
from .utils.constants import SECURITY_HEADERS, RATE_LIMIT_PER_MINUTE

logger = logging.getLogger(__name__)


def _register_blueprints(app: Flask) -> None:
    """Import and register all route blueprints.

    Args:
        app: The Flask application instance.
    """
    from .routes.analyze import analyze_bp
    from .routes.chat import chat_bp
    from .routes.compare import compare_bp
    from .routes.search import search_bp
    from .routes.translate import translate_bp
    from .routes.tts import tts_bp
    from .routes.history import history_bp
    from .routes.health import health_bp
    from .routes.negotiate import negotiate_bp
    from .routes.glossary import glossary_bp

    app.register_blueprint(analyze_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(compare_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(translate_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(negotiate_bp)
    app.register_blueprint(glossary_bp)


def _init_services(app: Flask, cfg: Config) -> None:
    """Initialise all backend service integrations.

    Args:
        app: The Flask application instance.
        cfg: Populated Config dataclass instance.
    """
    from .services import gemini_service, embedding_service
    from .services import mongodb_service, firebase_service
    from .services import translate_service, tts_service, search_service

    if cfg.GEMINI_API_KEY:
        gemini_service.init_gemini(cfg.GEMINI_API_KEY)
    else:
        logger.warning("GEMINI_API_KEY not set; AI features disabled.")

    if cfg.MONGO_URI:
        try:
            mongodb_service.init_mongo(cfg.MONGO_URI, cfg.MONGO_DB_NAME)
        except Exception as exc:
            logger.warning("MongoDB connection failed: %s. History disabled.", exc)
    else:
        logger.warning("MONGO_URI not set; history features disabled.")

    firebase_service.init_firebase(
        cfg.FIREBASE_SERVICE_ACCOUNT_JSON, cfg.FIREBASE_PROJECT_ID
    )

    translate_service.init_translate(
        cfg.GOOGLE_TRANSLATE_API_KEY, cfg.MYMEMORY_EMAIL
    )
    tts_service.init_tts(cfg.GOOGLE_TTS_API_KEY)
    search_service.init_search(cfg.GOOGLE_SEARCH_API_KEY, cfg.GOOGLE_SEARCH_ENGINE_ID)

    if cfg.TESSERACT_CMD:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = cfg.TESSERACT_CMD

    embedding_service.init_embedder()


def create_app(config: Optional[Config] = None) -> Flask:
    """Application factory — create and configure the Flask app.

    Args:
        config: Optional Config override (useful for testing).

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    cfg = config or Config()
    app.config["SECRET_KEY"] = cfg.SECRET_KEY
    app.config["TESTING"] = cfg.TESTING
    app.config["DEBUG"] = cfg.DEBUG
    app.config["LEXGUARD_CONFIG"] = cfg

    CORS(app, origins=cfg.CORS_ORIGINS, supports_credentials=True)

    Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[f"{RATE_LIMIT_PER_MINUTE} per minute"],
        storage_uri="memory://",
    )

    _init_services(app, cfg)
    _register_blueprints(app)

    @app.after_request
    def add_security_headers(response: Response) -> Response:
        """Attach security headers to every HTTP response."""
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response

    @app.errorhandler(404)
    def not_found(error):  # type: ignore[no-untyped-def]
        """Return JSON 404 without exposing stack traces."""
        return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):  # type: ignore[no-untyped-def]
        """Return JSON 405."""
        return jsonify({"error": "Method not allowed", "code": "METHOD_NOT_ALLOWED"}), 405

    @app.errorhandler(500)
    def internal_error(error):  # type: ignore[no-untyped-def]
        """Return JSON 500 without stack trace."""
        return jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}), 500

    logger.info("LexGuard application created successfully.")
    return app
