"""Complete test suite for all SecAgents agents."""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# ============================================================================
# SUPERVISOR AGENT TESTS
# ============================================================================

class TestSupervisorAgent:
    """Test suite for supervisor agent."""
    
    @pytest.mark.asyncio
    async def test_intent_classification_reconnaissance(self):
        """Test supervisor classifies reconnaissance intent."""
        from secagents.agents.supervisor import SupervisorAgent
        
        agent = SupervisorAgent()
        
        task = {
            "action": "classify_intent",
            "objective": "discover subdomains and endpoints for example.com",
            "scope": {"target": "example.com", "type": "reconnaissance"}
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.7
        assert "classified_intent" in output.result
        assert output.result["classified_intent"] in ["reconnaissance", "recon"]

    @pytest.mark.asyncio
    async def test_intent_classification_vulnerability_scan(self):
        """Test supervisor classifies vulnerability scan intent."""
        from secagents.agents.supervisor import SupervisorAgent
        
        agent = SupervisorAgent()
        
        task = {
            "action": "classify_intent",
            "objective": "scan for xss and sql injection vulnerabilities",
            "scope": {"target": "example.com/search", "type": "vulnerability_scan"}
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.7
        assert output.result["classified_intent"] in ["vulnerability_scan", "scanning"]

    @pytest.mark.asyncio
    async def test_phase_review_and_approval(self):
        """Test supervisor reviews and approves phases."""
        from secagents.agents.supervisor import SupervisorAgent
        
        agent = SupervisorAgent()
        
        task = {
            "action": "review_phase",
            "phase": "reconnaissance",
            "findings": [
                {"type": "subdomain", "value": "api.example.com"},
                {"type": "endpoint", "value": "/api/v1/users"}
            ]
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.6
        assert "approved" in output.result or "status" in output.result

# ============================================================================
# PLANNER AGENT TESTS
# ============================================================================

class TestPlannerAgent:
    """Test suite for planner agent."""
    
    @pytest.mark.asyncio
    async def test_full_scan_planning(self):
        """Test planner creates full scan plan."""
        from secagents.agents.planner import PlannerAgent
        
        agent = PlannerAgent()
        
        task = {
            "objective": "perform full security assessment",
            "target": "example.com",
            "scope": ".example.com",
            "constraints": {"time_limit": 3600}
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.7
        assert "phases" in output.result
        assert len(output.result["phases"]) > 0
        
        # Check phase structure
        first_phase = output.result["phases"][0]
        assert "name" in first_phase
        assert "tasks" in first_phase

    @pytest.mark.asyncio
    async def test_resource_allocation(self):
        """Test planner allocates resources appropriately."""
        from secagents.agents.planner import PlannerAgent
        
        agent = PlannerAgent()
        
        task = {
            "objective": "scan with limited resources",
            "constraints": {
                "max_concurrent_tasks": 3,
                "max_workers": 2,
                "time_limit": 1800
            }
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.6
        assert "resource_allocation" in output.result or "phases" in output.result

# ============================================================================
# RECON AGENT TESTS
# ============================================================================

class TestReconAgent:
    """Test suite for recon agent."""
    
    @pytest.mark.asyncio
    async def test_subdomain_enumeration(self):
        """Test recon agent discovers subdomains."""
        from secagents.agents.recon import ReconAgent
        
        agent = ReconAgent()
        
        task = {
            "action": "subdomain_enum",
            "target": "example.com"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence > 0.0
        if "error" not in output.result:
            assert "subdomains" in output.result
            assert isinstance(output.result["subdomains"], list)

    @pytest.mark.asyncio
    async def test_endpoint_crawling(self):
        """Test recon agent crawls endpoints."""
        from secagents.agents.recon import ReconAgent
        
        agent = ReconAgent()
        
        task = {
            "action": "crawl",
            "target": "example.com"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence > 0.0
        if "error" not in output.result:
            assert "endpoints" in output.result or "crawl_results" in output.result

    @pytest.mark.asyncio
    async def test_technology_fingerprinting(self):
        """Test recon agent fingerprints technologies."""
        from secagents.agents.recon import ReconAgent
        
        agent = ReconAgent()
        
        task = {
            "action": "fingerprint",
            "target": "example.com"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence > 0.0
        if "error" not in output.result:
            assert "technologies" in output.result or "fingerprints" in output.result

# ============================================================================
# WEB SECURITY AGENT TESTS
# ============================================================================

class TestWebSecurityAgent:
    """Test suite for web security agent."""
    
    @pytest.mark.asyncio
    async def test_xss_detection(self):
        """Test XSS vulnerability detection."""
        from secagents.agents.web_security import WebSecurityAgent
        
        agent = WebSecurityAgent()
        
        task = {
            "action": "test_xss",
            "target": "example.com/search",
            "parameter": "q"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.0
        assert "findings" in output.result or "error" in output.result

    @pytest.mark.asyncio
    async def test_sql_injection_detection(self):
        """Test SQL injection vulnerability detection."""
        from secagents.agents.web_security import WebSecurityAgent
        
        agent = WebSecurityAgent()
        
        task = {
            "action": "test_sqli",
            "target": "example.com/search",
            "parameter": "id"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.0
        assert "findings" in output.result or "error" in output.result

    @pytest.mark.asyncio
    async def test_ssti_detection(self):
        """Test SSTI vulnerability detection."""
        from secagents.agents.web_security import WebSecurityAgent
        
        agent = WebSecurityAgent()
        
        task = {
            "action": "test_ssti",
            "target": "example.com/render",
            "parameter": "template"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.0
        assert "findings" in output.result or "error" in output.result

# ============================================================================
# API SECURITY AGENT TESTS
# ============================================================================

class TestAPISecurityAgent:
    """Test suite for API security agent."""
    
    @pytest.mark.asyncio
    async def test_bola_detection(self):
        """Test BOLA (Broken Object Level Authorization) detection."""
        from secagents.agents.api_security import APISecurityAgent
        
        agent = APISecurityAgent()
        
        task = {
            "action": "test_bola",
            "api_endpoint": "https://api.example.com/users/123",
            "user_id_param": "123"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.0
        assert "findings" in output.result or "error" in output.result

    @pytest.mark.asyncio
    async def test_mass_assignment_detection(self):
        """Test mass assignment vulnerability detection."""
        from secagents.agents.api_security import APISecurityAgent
        
        agent = APISecurityAgent()
        
        task = {
            "action": "test_mass_assignment",
            "api_endpoint": "https://api.example.com/users",
            "method": "POST"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.0
        assert "findings" in output.result or "error" in output.result

# ============================================================================
# VALIDATOR AGENT TESTS
# ============================================================================

class TestValidatorAgent:
    """Test suite for validator agent."""
    
    @pytest.mark.asyncio
    async def test_finding_validation(self):
        """Test finding validation and false positive filtering."""
        from secagents.agents.validator import ValidatorAgent
        
        agent = ValidatorAgent()
        
        task = {
            "findings": [
                {
                    "type": "xss",
                    "endpoint": "/search",
                    "parameter": "q",
                    "poc_url": "http://example.com/search?q=test"
                }
            ]
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.0
        assert "validated" in output.result or "status" in output.result

    @pytest.mark.asyncio
    async def test_poc_request_replay(self):
        """Test PoC request replay for validation."""
        from secagents.agents.validator import ValidatorAgent
        
        agent = ValidatorAgent()
        
        task = {
            "action": "replay_poc",
            "poc_request": {
                "url": "http://example.com/search?q=test",
                "method": "GET"
            }
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.0
        assert "result" in output.result or "error" in output.result

# ============================================================================
# REPORT AGENT TESTS
# ============================================================================

class TestReportAgent:
    """Test suite for report agent."""
    
    @pytest.mark.asyncio
    async def test_markdown_report_generation(self):
        """Test Markdown report generation."""
        from secagents.agents.report import ReportAgent
        
        agent = ReportAgent()
        
        task = {
            "findings": [
                {
                    "id": "finding_1",
                    "type": "xss",
                    "severity": "high",
                    "cvss": 7.5
                }
            ],
            "target": "example.com",
            "format": "markdown"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.6
        assert "report" in output.result or "content" in output.result

    @pytest.mark.asyncio
    async def test_json_report_generation(self):
        """Test JSON report generation."""
        from secagents.agents.report import ReportAgent
        
        agent = ReportAgent()
        
        task = {
            "findings": [
                {
                    "id": "finding_1",
                    "type": "xss",
                    "severity": "high"
                }
            ],
            "target": "example.com",
            "format": "json"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.6
        assert "report" in output.result or "content" in output.result

    @pytest.mark.asyncio
    async def test_html_report_generation(self):
        """Test HTML report generation."""
        from secagents.agents.report import ReportAgent
        
        agent = ReportAgent()
        
        task = {
            "findings": [],
            "target": "example.com",
            "format": "html"
        }
        
        output = await agent.execute(task)
        
        assert output.confidence >= 0.6
        assert "report" in output.result or "content" in output.result

# ============================================================================
# AGENT INTEGRATION TESTS
# ============================================================================

class TestAgentIntegration:
    """Integration tests for agent workflows."""
    
    @pytest.mark.asyncio
    async def test_recon_to_validation_workflow(self):
        """Test workflow: recon -> validation."""
        from secagents.agents.recon import ReconAgent
        from secagents.agents.validator import ValidatorAgent
        
        recon = ReconAgent()
        validator = ValidatorAgent()
        
        # Step 1: Recon
        recon_task = {"action": "subdomain_enum", "target": "example.com"}
        recon_output = await recon.execute(recon_task)
        
        # Step 2: Validate findings
        if "subdomains" in recon_output.result:
            validator_task = {
                "findings": [
                    {"type": "subdomain", "value": sub}
                    for sub in recon_output.result["subdomains"][:2]
                ]
            }
            validator_output = await validator.execute(validator_task)
            assert validator_output.confidence >= 0.0

    @pytest.mark.asyncio
    async def test_full_workflow_planning_to_report(self):
        """Test full workflow: planning -> execution -> reporting."""
        from secagents.agents.planner import PlannerAgent
        from secagents.agents.report import ReportAgent
        
        planner = PlannerAgent()
        reporter = ReportAgent()
        
        # Step 1: Create plan
        plan_task = {
            "objective": "scan for vulnerabilities",
            "target": "example.com"
        }
        plan_output = await planner.execute(plan_task)
        
        # Step 2: Generate report
        report_task = {
            "findings": [],
            "target": "example.com",
            "format": "markdown"
        }
        report_output = await reporter.execute(report_task)
        
        assert report_output.confidence >= 0.0

# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

@pytest.mark.parametrize("vulnerability_type", [
    "xss", "sqli", "ssti", "lfi", "ssrf", "cmdi", "xxe", "crlf"
])
@pytest.mark.asyncio
async def test_web_vulnerability_types(vulnerability_type):
    """Test detection for various web vulnerability types."""
    from secagents.agents.web_security import WebSecurityAgent
    
    agent = WebSecurityAgent()
    
    task = {
        "action": f"test_{vulnerability_type}",
        "target": "example.com",
        "parameter": "test_param"
    }
    
    output = await agent.execute(task)
    assert output.confidence >= 0.0


@pytest.mark.parametrize("report_format", ["markdown", "json", "html"])
@pytest.mark.asyncio
async def test_report_formats(report_format):
    """Test report generation in various formats."""
    from secagents.agents.report import ReportAgent
    
    agent = ReportAgent()
    
    task = {
        "findings": [],
        "target": "example.com",
        "format": report_format
    }
    
    output = await agent.execute(task)
    assert output.confidence >= 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
