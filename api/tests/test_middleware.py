# ================================
# SensorPulse API - Middleware Unit Tests
# ================================

import time as _time
from unittest.mock import MagicMock

import pytest
from middleware import RateLimiter


def _make_request(ip: str = "127.0.0.1", user_id=None):
    """Create a mock Request with the needed attributes."""
    request = MagicMock()
    request.client.host = ip
    request.headers = {}

    state = MagicMock()
    state.user_id = user_id
    request.state = state

    return request


class TestRateLimiter:

    def test_allows_first_request(self):
        limiter = RateLimiter(requests_per_minute=5)
        allowed, headers = limiter.is_allowed(_make_request())
        assert allowed is True
        assert "X-RateLimit-Limit" in headers

    def test_blocks_after_limit_exceeded(self):
        limiter = RateLimiter(requests_per_minute=3)
        req = _make_request()
        for _ in range(3):
            limiter.is_allowed(req)
        allowed, headers = limiter.is_allowed(req)
        assert allowed is False
        assert "Retry-After" in headers

    def test_different_ips_have_separate_limits(self):
        limiter = RateLimiter(requests_per_minute=2)
        r1, r2 = _make_request("1.1.1.1"), _make_request("2.2.2.2")
        for _ in range(2):
            limiter.is_allowed(r1)
        # r1 is now at limit
        allowed_r1, _ = limiter.is_allowed(r1)
        allowed_r2, _ = limiter.is_allowed(r2)
        assert allowed_r1 is False
        assert allowed_r2 is True

    def test_user_id_takes_precedence_over_ip(self):
        limiter = RateLimiter(requests_per_minute=2)
        req = _make_request(ip="1.1.1.1", user_id="u1")
        key = limiter._get_client_key(req)
        assert key == "user:u1"

    def test_forwarded_for_header_used(self):
        limiter = RateLimiter(requests_per_minute=5)
        req = _make_request()
        req.headers = {"X-Forwarded-For": "10.0.0.1, 10.0.0.2"}
        req.state.user_id = None
        key = limiter._get_client_key(req)
        assert key == "ip:10.0.0.1"

    def test_remaining_decrements(self):
        limiter = RateLimiter(requests_per_minute=5)
        req = _make_request()
        _, h1 = limiter.is_allowed(req)
        _, h2 = limiter.is_allowed(req)
        assert int(h2["X-RateLimit-Remaining"]) < int(h1["X-RateLimit-Remaining"])
