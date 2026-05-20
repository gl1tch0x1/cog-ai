"""E2E pipeline test: exercises the full scan flow with mocked LLM and HTTP."""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

os.environ.setdefault("ALLOWED_DOMAINS", "example.com,*.example.com")
os.environ.setdefault("OLLAMA_HOST", "")


@pytest.fixture
def mock_llm_response():
    """Mock LLM that returns valid JSON consensus."""
    from secagents.llm.omni import LLMResponse
    return LLMResponse(
        content='{"valid": true, "confidence": 0.95, "severity": "high", "reason": "confirmed"}',
        provider="openai",
        model="gpt-4o-mini",
        tokens_used=50,
    )


@pytest.fixture
def mock_http_response():
    resp = MagicMock()
    resp.status_code = 200
    resp.text = "You have an error in your SQL syntax near '1'"
    resp.headers = {"content-type": "text/html"}
    return resp


@pytest.mark.asyncio
async def test_pipeline_scope_enforcement():
    """Pipeline rejects targets outside ALLOWED_DOMAINS."""
    from secagents.pipeline.runner import ScanPipeline

    pipeline = ScanPipeline(target="evil.com", depth="quick")
    with pytest.raises(SystemExit, match="Scope violation"):
        await pipeline.run()


@pytest.mark.asyncio
async def test_pipeline_runs_with_mocked_services(mock_llm_response, mock_http_response, tmp_path):
    """Full pipeline executes all phases with mocked external calls."""
    from secagents.pipeline.runner import ScanPipeline
    from secagents.llm.omni import OmniLLM, ProviderConfig

    # Mock all external dependencies
    with patch("secagents.pipeline.runner.ShodanIntel") as mock_shodan, \
         patch("secagents.pipeline.runner.ChaosIntel") as mock_chaos, \
         patch("secagents.pipeline.runner.FortressSandbox") as mock_sandbox, \
         patch("secagents.pipeline.runner.OmniLLM") as MockLLM, \
         patch("secagents.pipeline.runner.Vault") as MockVault, \
         patch("secagents.pipeline.runner.check_os_security_updates", return_value=(True, "OK")), \
         patch("secagents.arsenal.exploits.httpx.AsyncClient") as mock_http_client:

        # Configure mocks
        mock_shodan.return_value.available = False
        mock_chaos.return_value.available = False
        mock_sandbox.return_value.ensure_image.return_value = False

        vault_inst = MockVault.return_value
        vault_inst.validate_all = AsyncMock()
        vault_inst.print_status = MagicMock()
        vault_inst.any_llm_available = MagicMock(return_value=True)

        llm_inst = MockLLM.return_value
        llm_inst.providers = [ProviderConfig("openai", "sk-test")]
        llm_inst.complete = AsyncMock(return_value=mock_llm_response)
        llm_inst.aclose = AsyncMock()

        # Mock HTTP client for arsenal probes
        http_ctx = AsyncMock()
        http_ctx.get = AsyncMock(return_value=mock_http_response)
        http_ctx.__aenter__ = AsyncMock(return_value=http_ctx)
        http_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = http_ctx

        pipeline = ScanPipeline(
            target="example.com",
            depth="quick",
            workers=2,
            use_sandbox=False,
            skip_os_check=True,
            results_dir=tmp_path,
        )
        results = await pipeline.run()

        # Verify pipeline completed all phases
        assert results["domain"] == "example.com"
        assert "preflight" in results["phases"]
        assert "armada" in results["phases"]
        assert isinstance(results["findings"], list)
        assert isinstance(results["chains"], list)
        assert "reports" in results


@pytest.mark.asyncio
async def test_pipeline_crucible_rejects_unproven_findings(tmp_path):
    """Crucible rejects findings without deterministic proof."""
    from secagents.crucible.validation import CrucibleValidator
    from secagents.llm.consensus import ConsensusEngine, ConsensusResult

    consensus = MagicMock(spec=ConsensusEngine)
    consensus.verify_finding = AsyncMock(
        return_value=ConsensusResult(True, [], 1, 1, "ok")
    )

    validator = CrucibleValidator(consensus=consensus, verify_ssl=True)
    validator._client = AsyncMock()
    validator._client.get = AsyncMock(
        return_value=MagicMock(text="normal page content", status_code=200)
    )

    # Finding without proof should be rejected
    finding = {
        "url": "https://example.com/search",
        "source": "arsenal",
        "vuln_type": "sqli",
        "evidence": "",
        "proof_signal": "",
        "payload": "",
    }
    result = await validator.validate_finding(finding)
    assert result["validated"] is False
    assert result["false_positive"] is True

    # Finding WITH matching proof should pass
    validator._client.get = AsyncMock(
        return_value=MagicMock(text="You have an error in your SQL syntax", status_code=200)
    )
    finding_with_proof = {
        "url": "https://example.com/search?q=1'",
        "source": "cve_checks",
        "deterministic": True,
        "poc_url": "https://example.com/search?q=1'",
        "proof_signal": "error in your SQL syntax",
    }
    result = await validator.validate_finding(finding_with_proof)
    assert result["poc_verified"] is True
