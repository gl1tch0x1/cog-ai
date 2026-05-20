"""Tests for Vault key masking and provider detection."""

from secagents.vault.env_loader import mask_secret, detect_provider_from_key, KeyStatus


def test_mask_secret():
    assert mask_secret("sk-ant-api03-abcdefghijklmnop") == "sk-a...mnop"
    assert mask_secret("ab") == "***"


def test_detect_openai():
    assert detect_provider_from_key("sk-proj-abc123") == "openai"
    assert detect_provider_from_key("sk-abc123") == "openai"


def test_detect_anthropic():
    assert detect_provider_from_key("sk-ant-api03-xyz") == "anthropic"


def test_detect_groq():
    assert detect_provider_from_key("gsk_abc123") == "groq"


def test_detect_unknown_defaults_openai_compatible():
    assert detect_provider_from_key("custom-key-xyz") == "openai_compatible"
