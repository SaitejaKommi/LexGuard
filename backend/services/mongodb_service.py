"""
mongodb_service.py - MongoDB Atlas connection and CRUD helpers for LexGuard.

Manages a module-level connection pool via PyMongo and exposes typed helper
functions for every database operation used in the application.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from ..utils.constants import (
    MONGO_ANALYSES_COLLECTION,
    MONGO_SESSIONS_COLLECTION,
    MONGO_CHAT_COLLECTION,
    MONGO_USERS_COLLECTION,
)

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_db_name: str = "lexguard"


def init_mongo(uri: str, db_name: str) -> None:
    """Initialise the MongoDB connection pool.

    Args:
        uri: MongoDB Atlas connection string.
        db_name: Target database name.

    Raises:
        PyMongoError: If the initial connection attempt fails.
    """
    global _client, _db_name
    _client = MongoClient(uri, serverSelectionTimeoutMS=5000, maxPoolSize=10)
    _db_name = db_name
    _client.admin.command("ping")
    logger.info("MongoDB connection established to database '%s'.", db_name)


def _get_collection(name: str) -> Collection:
    """Return a collection handle, raising if not initialised.

    Args:
        name: Collection name.

    Returns:
        PyMongo Collection object.

    Raises:
        RuntimeError: If init_mongo has not been called.
    """
    if _client is None:
        raise RuntimeError("MongoDB is not initialised. Call init_mongo() first.")
    return _client[_db_name][name]


def save_analysis(
    user_email: str,
    filename: str,
    doc_hash: str,
    risk_score: int,
    clauses: list[dict],
    summary: str,
    raw_text_snippet: str,
) -> str:
    """Persist a completed contract analysis to the analyses collection.

    Args:
        user_email: Email address of the requesting user.
        filename: Original uploaded filename.
        doc_hash: SHA-256 hex digest of the document content.
        risk_score: Overall risk score (0-100).
        clauses: List of extracted clause dictionaries.
        summary: One-paragraph analysis summary.
        raw_text_snippet: First 500 chars of document text for preview.

    Returns:
        Inserted document ID as a string.

    Raises:
        PyMongoError: On database write failure.
    """
    col = _get_collection(MONGO_ANALYSES_COLLECTION)
    doc = {
        "user_email": user_email,
        "filename": filename,
        "doc_hash": doc_hash,
        "risk_score": risk_score,
        "clauses": clauses,
        "summary": summary,
        "raw_text_snippet": raw_text_snippet,
        "created_at": datetime.now(timezone.utc),
    }
    result = col.insert_one(doc)
    return str(result.inserted_id)


def get_analysis_by_hash(doc_hash: str) -> Optional[dict]:
    """Retrieve a cached analysis by document hash (cache hit check).

    Args:
        doc_hash: SHA-256 hex digest of the document.

    Returns:
        Analysis document dict, or None if not found.
    """
    col = _get_collection(MONGO_ANALYSES_COLLECTION)
    result = col.find_one({"doc_hash": doc_hash}, {"_id": 0})
    return result


def get_user_history(user_email: str, limit: int = 20) -> list[dict]:
    """Fetch the most recent analyses for a given user.

    Args:
        user_email: Email address of the requesting user.
        limit: Maximum number of records to return.

    Returns:
        List of analysis documents sorted newest-first.
    """
    col = _get_collection(MONGO_ANALYSES_COLLECTION)
    cursor = (
        col.find({"user_email": user_email}, {"_id": 0, "clauses": 0})
        .sort("created_at", DESCENDING)
        .limit(limit)
    )
    return list(cursor)


def get_analysis_by_id(analysis_id: str) -> Optional[dict]:
    """Retrieve a full analysis document by its MongoDB ObjectId string.

    Args:
        analysis_id: String representation of ObjectId.

    Returns:
        Full analysis document dict, or None if not found.
    """
    from bson import ObjectId

    col = _get_collection(MONGO_ANALYSES_COLLECTION)
    try:
        result = col.find_one({"_id": ObjectId(analysis_id)}, {"_id": 0})
        return result
    except Exception:
        return None


def save_chat_message(session_id: str, role: str, content: str) -> None:
    """Append a chat message to the session's conversation history.

    Args:
        session_id: Unique session identifier.
        role: Either 'user' or 'assistant'.
        content: Text content of the message.
    """
    col = _get_collection(MONGO_CHAT_COLLECTION)
    col.insert_one(
        {
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        }
    )


def get_chat_history(session_id: str, limit: int = 20) -> list[dict]:
    """Retrieve the most recent messages for a chat session.

    Args:
        session_id: Unique session identifier.
        limit: Maximum number of messages to return.

    Returns:
        List of message dicts with 'role' and 'content' keys.
    """
    col = _get_collection(MONGO_CHAT_COLLECTION)
    cursor = (
        col.find({"session_id": session_id}, {"_id": 0, "session_id": 0})
        .sort("created_at", DESCENDING)
        .limit(limit)
    )
    messages = list(cursor)
    messages.reverse()
    return messages


def upsert_user(email: str) -> None:
    """Create a user record if one does not already exist.

    Args:
        email: User's email address.
    """
    col = _get_collection(MONGO_USERS_COLLECTION)
    col.update_one(
        {"email": email},
        {
            "$setOnInsert": {
                "email": email,
                "created_at": datetime.now(timezone.utc),
            },
            "$set": {"last_seen": datetime.now(timezone.utc)},
        },
        upsert=True,
    )


def health_check() -> bool:
    """Verify that the MongoDB connection is alive.

    Returns:
        True if the ping command succeeds, False otherwise.
    """
    try:
        if _client is None:
            return False
        _client.admin.command("ping")
        return True
    except PyMongoError:
        return False


def compute_doc_hash(text: str) -> str:
    """Compute a SHA-256 hash of document text for cache keying.

    Args:
        text: Raw document text.

    Returns:
        Hexadecimal SHA-256 digest string.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
