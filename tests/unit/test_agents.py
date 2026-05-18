"""Unit tests for Python agents."""

import pytest
from secagents.agents.base import AgentOutput, AgentRole, RetryPolicy
from secagents.agents.planner import PlannerAgent
from secagents.agents.recon import ReconAgent
from secagents.agents.validator import ValidatorAgent
from secagents.agents.report import ReportAgent
from secagents.agents.supervisor import SupervisorAgent


@pytest.mark.asyncio
async def test_planner_generates_phases():
    agent = PlannerAgent()
    output = await agent.execute({"objective": "test", "scope": {"target": "example.com"}})
    assert output.confidence > 0
    assert "phases" in output.result
    assert len(output.result["phases"]) > 0


@pytest.mark.asyncio
async def test_recon_returns_structured_output():
    agent = ReconAgent()
    output = await agent.execute({"action": "subdomain_enum", "target": "example.com"})
    assert output.role == AgentRole.RECON
    assert "status" in output.result


@pytest.mark.asyncio
async def test_validator_filters_low_confidence():
    agent = ValidatorAgent()
    findings = [
        {"title": "XSS", "confidence": 0.9},
        {"title": "Maybe SQLi", "confidence": 0.3},
    ]
    output = await agent.execute({"findings": findings})
    assert len(output.result["validated"]) == 1
    assert len(output.result["rejected"]) == 1


@pytest.mark.asyncio
async def test_report_generates_markdown():
    agent = ReportAgent()
    findings = [{"title": "XSS", "severity": "high", "summary": "Reflected XSS",
                 "steps": "1. inject", "impact": "session hijack", "remediation": "encode output"}]
    output = await agent.execute({"findings": findings, "target": "example.com", "format": "markdown"})
    assert "# Security Assessment Report" in output.result["report"]


@pytest.mark.asyncio
async def test_supervisor_approves_completed_phase():
    agent = SupervisorAgent()
    output = await agent.execute({
        "action": "review",
        "workflow_state": {"current_phase": "recon", "completed_tasks": 5, "total_tasks": 5},
    })
    assert output.result["approved"] is True


def test_retry_policy_defaults():
    policy = RetryPolicy()
    assert policy.max_retries == 3
    assert policy.backoff_factor == 2.0
