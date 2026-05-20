"""Tests for ALLOWED_DOMAINS scope enforcement."""

import pytest

from secagents.infra.scope import (
    ScopePolicy,
    ScopeViolationError,
    enforce_scope,
    normalize_target,
    _domain_matches,
)


def test_normalize_url():
    assert normalize_target("https://api.example.com/path") == "api.example.com"


def test_wildcard_match():
    assert _domain_matches("sub.example.com", "*.example.com")
    assert not _domain_matches("evil.com", "*.example.com")


def test_enforce_scope_allowed(monkeypatch):
    monkeypatch.setenv("ALLOWED_DOMAINS", "example.com,*.test.com")
    assert enforce_scope("https://foo.test.com") == "foo.test.com"


def test_enforce_scope_denied(monkeypatch):
    monkeypatch.setenv("ALLOWED_DOMAINS", "example.com")
    with pytest.raises(ScopeViolationError):
        enforce_scope("https://evil.org")


def test_enforce_scope_empty_allowlist(monkeypatch):
    monkeypatch.delenv("ALLOWED_DOMAINS", raising=False)
    monkeypatch.setenv("ALLOWED_DOMAINS", "")
    with pytest.raises(ScopeViolationError):
        enforce_scope("example.com")


def test_blocked_domain(monkeypatch):
    monkeypatch.setenv("ALLOWED_DOMAINS", "example.com,internal.corp")
    monkeypatch.setenv("BLOCKED_DOMAINS", "internal.corp")
    with pytest.raises(ScopeViolationError):
        enforce_scope("internal.corp")
