"""Tests for Keyhacks agent with mocked HTTP."""

import pytest
from unittest.mock import AsyncMock, patch

from secagents.agents.keyhacks import KeyhacksAgent


def test_discover_github_token():
    agent = KeyhacksAgent()
    text = 'api_key = "ghp_123456789012345678901234567890123456"'
    found = agent.discover_keys(text)
    assert any(s == "github" for s, _ in found)


@pytest.mark.asyncio
async def test_validate_github_mocked():
    agent = KeyhacksAgent()
    key = "ghp_123456789012345678901234567890123456"

    mock_response = AsyncMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("secagents.agents.keyhacks.httpx.AsyncClient", return_value=mock_client):
        finding = await agent.validate_key("github", key)
        assert finding.valid is True
        assert "ghp_" in finding.key_masked or "..." in finding.key_masked


@pytest.mark.asyncio
async def test_throttle_enforced():
    agent = KeyhacksAgent()
    agent._min_interval = 0.01
    import time
    t0 = time.time()
    await agent._throttle()
    await agent._throttle()
    assert time.time() - t0 >= 0.01
