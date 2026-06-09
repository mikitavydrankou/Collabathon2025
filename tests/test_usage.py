"""Unit tests for shared.usage: the Redis-backed LLM spend cap fails open."""

from shared import usage


def _reset_client(monkeypatch):
    # usage caches its Redis client in a module global; clear it so each test
    # re-reads REDIS_URL.
    monkeypatch.setattr(usage, "_client", None)


def test_budget_not_exceeded_without_redis(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    _reset_client(monkeypatch)
    # Fail-open: with no Redis configured, requests are never blocked.
    assert usage.llm_budget_exceeded() is False


def test_usage_reports_disabled_without_redis(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("OPENAI_DAILY_LIMIT", "42")
    _reset_client(monkeypatch)
    result = usage.llm_usage()
    assert result == {"used": 0, "limit": 42, "enabled": False}


def test_usage_default_limit(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("OPENAI_DAILY_LIMIT", raising=False)
    _reset_client(monkeypatch)
    assert usage.llm_usage()["limit"] == 500
