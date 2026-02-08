"""
Tests for secrets/config handling: no secrets in logs, URLs masked, context redacted.

Run: pytest tests/test_secrets_config.py -v
"""

import pytest

from app.shared.cache.redis_client import mask_redis_url
from app.shared.utils.sanitize import (
    redact_sensitive_dict,
    is_sensitive_key,
)


class TestMaskRedisUrl:
    """Redis URL is masked in logs so passwords are not exposed."""

    def test_no_password_unchanged(self):
        assert mask_redis_url("redis://localhost:6379/0") == "redis://localhost:6379/0"

    def test_password_masked(self):
        out = mask_redis_url("redis://:secret123@host.example.com:6379/0")
        assert out == "redis://***@host.example.com:6379/0"
        assert "secret123" not in out

    def test_empty_returns_as_is(self):
        assert mask_redis_url("") == ""


class TestRedactSensitiveDict:
    """Exception context and similar dicts are redacted before logging."""

    def test_redacts_password(self):
        data = {"user": "alice", "password": "s3cr3t"}
        out = redact_sensitive_dict(data)
        assert out["user"] == "alice"
        assert out["password"] == "[REDACTED]"

    def test_redacts_nested(self):
        data = {"error": {"api_key": "key123", "msg": "bad request"}}
        out = redact_sensitive_dict(data)
        assert out["error"]["api_key"] == "[REDACTED]"
        assert out["error"]["msg"] == "bad request"

    def test_redacts_case_insensitive(self):
        data = {"API_KEY": "xyz", "Token": "abc"}
        out = redact_sensitive_dict(data)
        assert out["API_KEY"] == "[REDACTED]"
        assert out["Token"] == "[REDACTED]"

    def test_non_sensitive_unchanged(self):
        data = {"name": "test", "count": 42}
        out = redact_sensitive_dict(data)
        assert out == data

    def test_none_unchanged(self):
        assert redact_sensitive_dict(None) is None


class TestIsSensitiveKey:
    """Sensitive key detection for validation error redaction."""

    def test_sensitive_keys(self):
        assert is_sensitive_key("password") is True
        assert is_sensitive_key("api_key") is True
        assert is_sensitive_key("PASSWORD") is True

    def test_non_sensitive(self):
        assert is_sensitive_key("email") is False
        assert is_sensitive_key("name") is False
