"""Tests for Omni-LLM client and consensus."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from secagents.llm.omni import OmniLLM, ProviderConfig
from secagents.llm.consensus import ConsensusEngine


def test_provider_discovery_from_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEYS", "sk-test123,sk-ant-test456")
    llm = OmniLLM()
    assert len(llm.providers) == 2
    assert llm.providers[0].name == "openai"
    assert llm.providers[1].name == "anthropic"


@pytest.mark.asyncio
async def test_consensus_single_provider():
    llm = OmniLLM(providers=[ProviderConfig("openai", "sk-test", model="gpt-4o-mini")])

    async def mock_complete(messages, provider=None, model=None, max_tokens=2048):
        from secagents.llm.omni import LLMResponse
        return LLMResponse(
            content='{"valid": true, "confidence": 0.9, "reason": "test"}',
            provider="openai",
            model="gpt-4o-mini",
        )

    llm.complete = mock_complete
    engine = ConsensusEngine(llm=llm, min_agreement=1)
    result = await engine.verify_finding({"title": "SQLi", "url": "http://test"})
    assert result.agreed is True


@pytest.mark.asyncio
async def test_consensus_multi_provider_agreement():
    providers = [
        ProviderConfig("openai", "sk-1"),
        ProviderConfig("anthropic", "sk-ant-2"),
        ProviderConfig("groq", "gsk_3"),
    ]
    llm = OmniLLM(providers=providers)

    async def mock_complete(messages, provider=None, model=None, max_tokens=2048):
        from secagents.llm.omni import LLMResponse
        return LLMResponse(
            content='{"valid": true, "confidence": 0.95, "reason": "confirmed"}',
            provider=provider or "openai",
            model="test",
        )

    llm.complete = mock_complete
    engine = ConsensusEngine(llm=llm, min_agreement=2)
    result = await engine.verify_finding({"title": "XSS"})
    assert result.agreed is True
    assert result.agreement_count >= 2
