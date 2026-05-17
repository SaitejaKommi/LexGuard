"""
embedding_service.py - Sentence-transformer embeddings for RAG-style clause similarity.

Embeds extracted clauses and compares them against a curated database of
standard fair clauses to detect unusually restrictive language.
"""

import logging
from typing import Optional

import numpy as np

from ..utils.constants import EMBEDDING_MODEL, SIMILARITY_THRESHOLD, STANDARD_FAIR_CLAUSES

logger = logging.getLogger(__name__)

_embedder = None
_standard_embeddings: Optional[np.ndarray] = None


def init_embedder() -> None:
    """Schedule lazy background loading of the sentence-transformer model.

    Starts a daemon thread to load the model without blocking app startup.
    """
    import threading

    def _load():
        global _embedder, _standard_embeddings
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer(EMBEDDING_MODEL)
            _standard_embeddings = _embedder.encode(STANDARD_FAIR_CLAUSES, convert_to_numpy=True)
            logger.info("Sentence-transformer model '%s' loaded in background.", EMBEDDING_MODEL)
        except ImportError as exc:
            logger.warning("sentence-transformers not installed; RAG disabled. %s", exc)
        except Exception as exc:
            logger.warning("Embedder failed to load: %s", exc)

    t = threading.Thread(target=_load, daemon=True, name="embedder-loader")
    t.start()
    logger.info("Embedder loading started in background thread.")


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First embedding vector.
        b: Second embedding vector.

    Returns:
        Cosine similarity value in range [-1, 1].
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _get_best_match(clause_embedding: np.ndarray) -> tuple[float, str]:
    """Find the most similar standard clause for a given embedding.

    Args:
        clause_embedding: Embedding vector for the contract clause.

    Returns:
        Tuple of (best_similarity_score, matched_standard_clause_text).
    """
    if _standard_embeddings is None:
        return 0.0, ""

    similarities = np.array(
        [_cosine_similarity(clause_embedding, std) for std in _standard_embeddings]
    )
    best_idx = int(np.argmax(similarities))
    return float(similarities[best_idx]), STANDARD_FAIR_CLAUSES[best_idx]


def compute_clause_similarities(clauses: list[dict]) -> list[dict]:
    """Compute similarity scores between contract clauses and standard fair clauses.

    Args:
        clauses: List of clause dicts with at least a 'clause_text' key.

    Returns:
        Updated clause list with added similarity fields:
            - similarity_score: float 0.0–1.0
            - deviation_percent: how much more restrictive vs. standard
            - matched_standard: text of the closest standard clause
            - similarity_flag: bool indicating unusual restriction
    """
    if _embedder is None:
        logger.warning("Embedder not loaded; returning clauses without similarity scores.")
        for clause in clauses:
            clause["similarity_score"] = None
            clause["deviation_percent"] = None
            clause["matched_standard"] = None
            clause["similarity_flag"] = False
        return clauses

    texts = [c.get("clause_text", "") for c in clauses]
    embeddings = _embedder.encode(texts, convert_to_numpy=True)

    for i, clause in enumerate(clauses):
        sim_score, matched = _get_best_match(embeddings[i])
        deviation = max(0, int((1 - sim_score) * 100))
        clause["similarity_score"] = round(sim_score, 4)
        clause["deviation_percent"] = deviation
        clause["matched_standard"] = matched
        clause["similarity_flag"] = sim_score < SIMILARITY_THRESHOLD

    return clauses


def is_embedder_available() -> bool:
    """Check whether the sentence-transformer model is loaded and ready.

    Returns:
        True if embedder is available, False otherwise.
    """
    return _embedder is not None
