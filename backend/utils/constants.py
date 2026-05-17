"""
constants.py - All hardcoded constants for LexGuard backend.

This module centralizes every magic number, string literal, and configuration
constant used across the application to maintain a single source of truth.
"""

from typing import Final

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
APP_NAME: Final[str] = "LexGuard"
APP_VERSION: Final[str] = "1.0.0"
APP_DESCRIPTION: Final[str] = "AI-powered contract intelligence platform"

# ---------------------------------------------------------------------------
# File upload constraints
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS: Final[set] = {"pdf", "docx", "txt"}
ALLOWED_MIME_TYPES: Final[set] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

# Magic bytes for file type validation
PDF_MAGIC: Final[bytes] = b"%PDF"
DOCX_MAGIC: Final[bytes] = b"PK\x03\x04"

# ---------------------------------------------------------------------------
# Text length limits
# ---------------------------------------------------------------------------
MAX_CONTRACT_TEXT_LENGTH: Final[int] = 50_000
MAX_CHAT_MESSAGE_LENGTH: Final[int] = 1_000
MAX_SEARCH_QUERY_LENGTH: Final[int] = 500
MAX_FILENAME_LENGTH: Final[int] = 255

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
RATE_LIMIT_PER_MINUTE: Final[int] = 20
RATE_LIMIT_STORAGE: Final[str] = "memory://"

# ---------------------------------------------------------------------------
# Caching TTL (seconds)
# ---------------------------------------------------------------------------
ANALYSIS_CACHE_TTL: Final[int] = 600   # 10 minutes
SEARCH_CACHE_TTL: Final[int] = 600     # 10 minutes
EMBEDDING_CACHE_TTL: Final[int] = 3600  # 1 hour

# ---------------------------------------------------------------------------
# Risk scoring thresholds
# ---------------------------------------------------------------------------
RISK_SCORE_CRITICAL_MIN: Final[int] = 80
RISK_SCORE_HIGH_MIN: Final[int] = 60
RISK_SCORE_MEDIUM_MIN: Final[int] = 40
RISK_SCORE_LOW_MIN: Final[int] = 20

RISK_LEVELS: Final[list] = ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

RISK_LEVEL_WEIGHTS: Final[dict] = {
    "CRITICAL": 100,
    "HIGH": 75,
    "MEDIUM": 50,
    "LOW": 25,
    "SAFE": 0,
}

# ---------------------------------------------------------------------------
# Clause categories
# ---------------------------------------------------------------------------
CLAUSE_CATEGORIES: Final[list] = [
    "Employment",
    "Privacy",
    "IP Rights",
    "Financial",
    "Termination",
    "Arbitration",
    "Liability",
    "Non-Compete",
    "Data Collection",
    "Renewal",
    "Confidentiality",
    "Indemnification",
    "Governing Law",
    "Other",
]

# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES: Final[dict] = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "ar": "Arabic",
    "te": "Telugu",
}

# ---------------------------------------------------------------------------
# Gemini model settings
# ---------------------------------------------------------------------------
GEMINI_MODEL: Final[str] = "gemini-1.5-flash"
GEMINI_MAX_OUTPUT_TOKENS: Final[int] = 8192
GEMINI_TEMPERATURE: Final[float] = 0.1

# ---------------------------------------------------------------------------
# MongoDB collections
# ---------------------------------------------------------------------------
MONGO_ANALYSES_COLLECTION: Final[str] = "analyses"
MONGO_SESSIONS_COLLECTION: Final[str] = "sessions"
MONGO_CHAT_COLLECTION: Final[str] = "chat_history"
MONGO_USERS_COLLECTION: Final[str] = "users"

# ---------------------------------------------------------------------------
# Sentence-transformer model
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: Final[str] = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD: Final[float] = 0.75

# ---------------------------------------------------------------------------
# TTS settings
# ---------------------------------------------------------------------------
TTS_LANGUAGE_CODE: Final[str] = "en-US"
TTS_VOICE_NAME: Final[str] = "en-US-Neural2-D"
TTS_AUDIO_ENCODING: Final[str] = "MP3"

# ---------------------------------------------------------------------------
# HTTP headers
# ---------------------------------------------------------------------------
SECURITY_HEADERS: Final[dict] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com "
        "https://www.google-analytics.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "connect-src 'self' https://www.google-analytics.com;"
    ),
}

# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------
ERROR_CODES: Final[dict] = {
    "INVALID_FILE_TYPE": "The uploaded file type is not supported.",
    "FILE_TOO_LARGE": "The uploaded file exceeds the 10 MB size limit.",
    "TEXT_TOO_LONG": "The contract text exceeds the maximum allowed length.",
    "RATE_LIMIT_EXCEEDED": "Too many requests. Please try again later.",
    "GEMINI_ERROR": "AI analysis service encountered an error.",
    "PARSE_ERROR": "Could not parse the uploaded document.",
    "MONGO_ERROR": "Database operation failed.",
    "INVALID_INPUT": "The provided input is invalid or malformed.",
    "MISSING_FIELD": "A required field is missing from the request.",
    "SESSION_NOT_FOUND": "No active session found for this user.",
    "ANALYSIS_NOT_FOUND": "The requested analysis could not be found.",
    "TRANSLATION_ERROR": "Translation service encountered an error.",
    "TTS_ERROR": "Text-to-speech service encountered an error.",
    "SEARCH_ERROR": "Legal search service encountered an error.",
}

# ---------------------------------------------------------------------------
# Standard fair clauses database (for RAG similarity)
# ---------------------------------------------------------------------------
STANDARD_FAIR_CLAUSES: Final[list] = [
    "Either party may terminate this agreement with 30 days written notice.",
    "Confidential information shall remain protected for a period of 2 years following termination.",
    "The employee retains ownership of all intellectual property created outside working hours using personal resources.",
    "Disputes shall be resolved through mediation before proceeding to arbitration.",
    "Limitation of liability shall not exceed the total fees paid in the preceding 12 months.",
    "Non-compete restrictions shall be limited to a 6-month period within the employee's direct market.",
    "Personal data shall be collected only for specified purposes and not shared with third parties without consent.",
    "Automatic renewal requires written notice to cancel at least 30 days before renewal date.",
    "Arbitration shall be conducted by a neutral arbitrator agreed upon by both parties.",
    "Indemnification obligations apply only to proven negligence or willful misconduct.",
    "Governing law shall be mutually agreed upon and specified in writing.",
    "Payment terms shall be net 30 from invoice date.",
    "Severance compensation shall be paid for involuntary termination without cause.",
    "Intellectual property created during employment belongs to the employer only when using company resources.",
    "Class action rights shall be preserved for consumer protection claims.",
]

# ---------------------------------------------------------------------------
# Search fallback results
# ---------------------------------------------------------------------------
SEARCH_FALLBACK_RESULTS: Final[list] = [
    {
        "title": "FTC Non-Compete Rule 2024 — Federal Trade Commission",
        "snippet": "The FTC issued a rule banning most non-compete agreements, finding them unfair methods of competition.",
        "link": "https://www.ftc.gov/legal-library/browse/rules/non-compete-clause-rule",
    },
    {
        "title": "GDPR Data Collection Standards — European Commission",
        "snippet": "GDPR requires lawful basis for data collection, purpose limitation, and explicit consent for sensitive data.",
        "link": "https://commission.europa.eu/law/law-topic/data-protection_en",
    },
    {
        "title": "Arbitration Clauses in Consumer Contracts — Consumer Financial Protection Bureau",
        "snippet": "CFPB research on arbitration agreements and their impact on consumers' ability to seek legal redress.",
        "link": "https://www.consumerfinance.gov/data-research/research-reports/arbitration-study/",
    },
    {
        "title": "Intellectual Property Assignment in Employment — USPTO",
        "snippet": "Guidance on IP assignment clauses and what employers can and cannot claim ownership of.",
        "link": "https://www.uspto.gov/learning-and-resources/ip-policy",
    },
    {
        "title": "Standard Employment Contract Clauses — SHRM",
        "snippet": "Society for Human Resource Management guide on fair employment contract terms and best practices.",
        "link": "https://www.shrm.org/resourcesandtools/tools-and-samples/policies",
    },
    {
        "title": "Limitation of Liability Clauses — Legal Information Institute",
        "snippet": "Cornell Law School explanation of limitation of liability clauses and their enforceability.",
        "link": "https://www.law.cornell.edu/wex/limitation_of_liability",
    },
]
