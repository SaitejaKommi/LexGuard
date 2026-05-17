"""
rate_limiter.py - In-memory rate limiter for LexGuard routes.

Uses a sliding window counter keyed by session ID.  Flask-Limiter is
configured in app.py; this module provides helper utilities for manual
checks and testing.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from .constants import RATE_LIMIT_PER_MINUTE


class RateLimiter:
    """Thread-safe sliding-window rate limiter.

    Each key (typically a session ID or IP address) is allowed at most
    *limit* requests within *window_seconds*.
    """

    def __init__(
        self, limit: int = RATE_LIMIT_PER_MINUTE, window_seconds: int = 60
    ) -> None:
        """Initialise the rate limiter.

        Args:
            limit: Maximum number of requests allowed per window.
            window_seconds: Length of the sliding window in seconds.
        """
        self._limit = limit
        self._window = window_seconds
        self._requests: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        """Check whether *key* is within the rate limit.

        Removes expired timestamps and records the current request.

        Args:
            key: Unique identifier for the requester (session ID / IP).

        Returns:
            True if the request is allowed, False if rate-limited.
        """
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
            if len(timestamps) >= self._limit:
                return False
            timestamps.append(now)
            return True

    def remaining(self, key: str) -> int:
        """Return the number of requests *key* may still make this window.

        Args:
            key: Unique identifier for the requester.

        Returns:
            Remaining request count (0 if rate-limited).
        """
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
            return max(0, self._limit - len(timestamps))

    def reset(self, key: str) -> None:
        """Clear all recorded requests for *key* (useful in testing).

        Args:
            key: Unique identifier to reset.
        """
        with self._lock:
            self._requests.pop(key, None)


# Module-level singleton used by Flask routes
_global_limiter = RateLimiter()


def check_rate_limit(key: str) -> bool:
    """Convenience wrapper around the global RateLimiter instance.

    Args:
        key: Unique identifier for the requester.

    Returns:
        True if request is allowed, False if rate-limited.
    """
    return _global_limiter.is_allowed(key)


def get_remaining(key: str) -> int:
    """Return remaining requests for *key* using the global limiter.

    Args:
        key: Unique identifier for the requester.

    Returns:
        Number of remaining allowed requests.
    """
    return _global_limiter.remaining(key)


def reset_key(key: str) -> None:
    """Reset rate-limit counter for *key* on the global limiter.

    Args:
        key: Unique identifier to reset.
    """
    _global_limiter.reset(key)
