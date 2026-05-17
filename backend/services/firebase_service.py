"""
firebase_service.py - Google Firebase Firestore integration for LexGuard.

Acts as a secondary/backup persistence layer alongside MongoDB Atlas.
Provides graceful degradation if Firebase credentials are not configured.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

_firestore_client = None
_firebase_available: bool = False


def init_firebase(service_account_json: Optional[str], project_id: str) -> None:
    """Initialise Firebase Admin SDK and Firestore client.

    Args:
        service_account_json: JSON string of service account credentials.
        project_id: Firebase project ID.
    """
    global _firestore_client, _firebase_available
    if not service_account_json or not project_id:
        logger.info("Firebase credentials not provided; Firebase disabled.")
        return
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred_dict = json.loads(service_account_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        _firestore_client = firestore.client()
        _firebase_available = True
        logger.info("Firebase Firestore initialised for project '%s'.", project_id)
    except Exception as exc:
        logger.warning("Firebase initialisation failed: %s. Continuing without Firebase.", exc)


def _get_client():
    """Return the Firestore client or raise if not available.

    Returns:
        Firestore client object.

    Raises:
        RuntimeError: If Firebase is not initialised.
    """
    if not _firebase_available or _firestore_client is None:
        raise RuntimeError("Firebase Firestore is not available.")
    return _firestore_client


def backup_analysis_to_firestore(
    analysis_id: str, user_email: str, risk_score: int, summary: str
) -> bool:
    """Write a lightweight analysis backup record to Firestore.

    Args:
        analysis_id: MongoDB document ID used as Firestore document ID.
        user_email: User email for grouping.
        risk_score: Overall risk score.
        summary: Analysis summary paragraph.

    Returns:
        True if backup succeeded, False otherwise.
    """
    try:
        db = _get_client()
        db.collection("analyses").document(analysis_id).set(
            {
                "user_email": user_email,
                "risk_score": risk_score,
                "summary": summary,
                "backed_up_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return True
    except Exception as exc:
        logger.warning("Firestore backup failed: %s", exc)
        return False


def get_user_analyses_from_firestore(user_email: str) -> list[dict]:
    """Retrieve analysis backup records from Firestore for a user.

    Args:
        user_email: User's email address.

    Returns:
        List of Firestore analysis documents, empty if unavailable.
    """
    try:
        db = _get_client()
        docs = (
            db.collection("analyses")
            .where("user_email", "==", user_email)
            .order_by("backed_up_at", direction="DESCENDING")
            .limit(10)
            .stream()
        )
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as exc:
        logger.warning("Firestore retrieval failed: %s", exc)
        return []


def is_firebase_available() -> bool:
    """Check whether Firebase Firestore is available.

    Returns:
        True if Firestore client is ready, False otherwise.
    """
    return _firebase_available
