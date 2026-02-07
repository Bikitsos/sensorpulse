# ================================
# SensorPulse API - Auth Unit Tests
# ================================

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from auth import create_access_token, decode_access_token


class TestCreateAccessToken:
    """Tests for JWT token creation."""

    def test_returns_token_and_expiry(self):
        token, expires_in = create_access_token("user123", "user@example.com")
        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(expires_in, int)
        assert expires_in > 0

    def test_token_can_be_decoded(self):
        uid = str(uuid.uuid4())
        token, _ = create_access_token(uid, "user@example.com")
        data = decode_access_token(token)
        assert data is not None
        assert data.user_id == uid
        assert data.email == "user@example.com"

    def test_token_expiry_is_in_future(self):
        token, _ = create_access_token("u1", "a@b.com")
        data = decode_access_token(token)
        assert data.exp > datetime.now(timezone.utc)


class TestDecodeAccessToken:
    """Tests for JWT token decoding."""

    def test_returns_none_for_invalid_token(self):
        assert decode_access_token("not.a.jwt") is None

    def test_returns_none_for_empty_string(self):
        assert decode_access_token("") is None

    def test_returns_none_for_tampered_token(self):
        token, _ = create_access_token("uid", "e@e.com")
        # Flip a character in the payload section
        parts = token.split(".")
        parts[1] = parts[1][:-1] + ("A" if parts[1][-1] != "A" else "B")
        tampered = ".".join(parts)
        assert decode_access_token(tampered) is None
