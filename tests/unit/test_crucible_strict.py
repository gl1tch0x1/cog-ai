"""Tests for strict Crucible validation rules."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from secagents.crucible.validation import CrucibleValidator
from secagents.llm.consensus import ConsensusEngine, ConsensusResult


@pytest.mark.asyncio
async def test_rejects_arsenal_without_proof():
    consensus = MagicMock(spec=ConsensusEngine)
    consensus.verify_finding = AsyncMock(
        return_value=ConsensusResult(True, [], 1, 1, "ok")
    )
    crucible = CrucibleValidator(consensus=consensus, verify_ssl=True)
    crucible._client = AsyncMock()
    crucible._client.get = AsyncMock(return_value=MagicMock(text="ok", status_code=200))

    finding = {
        "url": "https://example.com",
        "source": "arsenal",
        "evidence": "",
        "proof_signal": "",
    }
    result = await crucible.validate_finding(finding)
    assert result["validated"] is False
    assert result["false_positive"] is True


@pytest.mark.asyncio
async def test_accepts_deterministic_with_proof():
    consensus = MagicMock(spec=ConsensusEngine)
    consensus.verify_finding = AsyncMock(
        return_value=ConsensusResult(True, [], 1, 1, "ok")
    )
    crucible = CrucibleValidator(consensus=consensus, verify_ssl=True)
    crucible._client = AsyncMock()
    crucible._client.get = AsyncMock(
        return_value=MagicMock(text="mysql syntax error", status_code=200)
    )

    finding = {
        "url": "https://example.com",
        "poc_url": "https://example.com?q=1'",
        "source": "cve_checks",
        "deterministic": True,
        "proof_signal": "mysql syntax",
    }
    result = await crucible.validate_finding(finding)
    assert result["poc_verified"] is True
