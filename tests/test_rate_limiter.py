"""test_rate_limiter.py - Tests for the rate limiter utility."""
import pytest
from backend.utils.rate_limiter import RateLimiter


def test_allows_requests_within_limit():
    limiter = RateLimiter(limit=5, window_seconds=60)
    for _ in range(5):
        assert limiter.is_allowed("user1") is True


def test_blocks_request_over_limit():
    limiter = RateLimiter(limit=3, window_seconds=60)
    for _ in range(3):
        limiter.is_allowed("user2")
    assert limiter.is_allowed("user2") is False


def test_different_keys_are_independent():
    limiter = RateLimiter(limit=2, window_seconds=60)
    limiter.is_allowed("a")
    limiter.is_allowed("a")
    assert limiter.is_allowed("b") is True


def test_reset_clears_counter():
    limiter = RateLimiter(limit=2, window_seconds=60)
    limiter.is_allowed("user3")
    limiter.is_allowed("user3")
    limiter.reset("user3")
    assert limiter.is_allowed("user3") is True


def test_remaining_decreases():
    limiter = RateLimiter(limit=5, window_seconds=60)
    before = limiter.remaining("user4")
    limiter.is_allowed("user4")
    after = limiter.remaining("user4")
    assert after == before - 1
