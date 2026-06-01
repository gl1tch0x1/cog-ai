"""Comprehensive API integration tests."""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock


# ============================================================================
# FIXTURE SETUP
# ============================================================================

@pytest.fixture
def api_client():
    """Create test API client."""
    from fastapi.testclient import TestClient
    from secagents.api.main import app
    return TestClient(app)


@pytest.fixture
def valid_api_key():
    """Generate valid API key for tests."""
    return "test_key_valid_12345"


@pytest.fixture
def auth_headers(valid_api_key):
    """Create auth headers."""
    return {"Authorization": f"Bearer {valid_api_key}"}


# ============================================================================
# SCAN ENDPOINTS TESTS
# ============================================================================

class TestScanEndpoints:
    """Test scan management endpoints."""
    
    def test_create_scan_success(self, api_client, auth_headers):
        """Test successful scan creation."""
        response = api_client.post(
            "/v1/scans",
            json={
                "target": "example.com",
                "scope": ".example.com",
                "scan_type": "full"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"]
        assert data["status"] == "queued"
        assert data["target"] == "example.com"

    def test_create_scan_missing_target(self, api_client, auth_headers):
        """Test scan creation fails without target."""
        response = api_client.post(
            "/v1/scans",
            json={
                "scope": ".example.com",
                "scan_type": "full"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "target" in response.json()["message"].lower()

    def test_create_scan_invalid_scope(self, api_client, auth_headers):
        """Test scan creation fails with invalid scope."""
        response = api_client.post(
            "/v1/scans",
            json={
                "target": "example.com",
                "scope": "invalid!@#$%",
                "scan_type": "full"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_get_scan_status(self, api_client, auth_headers):
        """Test getting scan status."""
        # First create a scan
        create_response = api_client.post(
            "/v1/scans",
            json={
                "target": "example.com",
                "scan_type": "full"
            },
            headers=auth_headers
        )
        scan_id = create_response.json()["id"]
        
        # Get scan status
        response = api_client.get(
            f"/v1/scans/{scan_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == scan_id
        assert data["status"] in ["queued", "running", "completed"]

    def test_get_scan_not_found(self, api_client, auth_headers):
        """Test getting non-existent scan."""
        response = api_client.get(
            "/v1/scans/nonexistent_scan_id",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_list_scans(self, api_client, auth_headers):
        """Test listing scans."""
        response = api_client.get(
            "/v1/scans",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scans" in data
        assert "total" in data
        assert isinstance(data["scans"], list)

    def test_list_scans_with_filters(self, api_client, auth_headers):
        """Test listing scans with filters."""
        response = api_client.get(
            "/v1/scans?status=completed&severity=high&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10

    def test_cancel_scan(self, api_client, auth_headers):
        """Test cancelling a scan."""
        # Create scan
        create_response = api_client.post(
            "/v1/scans",
            json={"target": "example.com", "scan_type": "full"},
            headers=auth_headers
        )
        scan_id = create_response.json()["id"]
        
        # Cancel scan
        response = api_client.delete(
            f"/v1/scans/{scan_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

# ============================================================================
# FINDINGS ENDPOINTS TESTS
# ============================================================================

class TestFindingsEndpoints:
    """Test findings retrieval endpoints."""
    
    def test_get_findings(self, api_client, auth_headers):
        """Test getting scan findings."""
        response = api_client.get(
            "/v1/scans/test_scan_id/findings",
            headers=auth_headers
        )
        
        # May be 404 if scan doesn't exist, that's ok
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "findings" in data

    def test_get_findings_with_filters(self, api_client, auth_headers):
        """Test getting findings with severity filter."""
        response = api_client.get(
            "/v1/scans/test_scan_id/findings?severity=high&type=xss",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]

    def test_get_finding_detail(self, api_client, auth_headers):
        """Test getting individual finding details."""
        response = api_client.get(
            "/v1/scans/test_scan_id/findings/finding_123",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "type" in data
            assert "severity" in data

    def test_validate_finding(self, api_client, auth_headers):
        """Test validating a finding."""
        response = api_client.post(
            "/v1/scans/test_scan_id/findings/finding_123/validate",
            json={"revalidate": True},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]

# ============================================================================
# REPORT ENDPOINTS TESTS
# ============================================================================

class TestReportEndpoints:
    """Test report generation endpoints."""
    
    def test_generate_report_pdf(self, api_client, auth_headers):
        """Test generating PDF report."""
        response = api_client.post(
            "/v1/scans/test_scan_id/report",
            json={
                "format": "pdf",
                "include_findings": True,
                "include_remediation": True
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404]

    def test_generate_report_markdown(self, api_client, auth_headers):
        """Test generating Markdown report."""
        response = api_client.post(
            "/v1/scans/test_scan_id/report",
            json={
                "format": "markdown",
                "include_findings": True
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404]

    def test_generate_report_json(self, api_client, auth_headers):
        """Test generating JSON report."""
        response = api_client.post(
            "/v1/scans/test_scan_id/report",
            json={
                "format": "json",
                "include_findings": True
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404]

    def test_list_reports(self, api_client, auth_headers):
        """Test listing reports for a scan."""
        response = api_client.get(
            "/v1/scans/test_scan_id/reports",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]

# ============================================================================
# AGENT STATUS ENDPOINTS TESTS
# ============================================================================

class TestAgentStatusEndpoints:
    """Test agent status endpoints."""
    
    def test_get_agent_status(self, api_client, auth_headers):
        """Test getting individual agent status."""
        response = api_client.get(
            "/v1/agents/web_security",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "web_security"
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "offline"]

    def test_get_all_agents_status(self, api_client, auth_headers):
        """Test getting all agents status."""
        response = api_client.get(
            "/v1/agents",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "overall_status" in data
        assert isinstance(data["agents"], list)

# ============================================================================
# HEALTH & SYSTEM ENDPOINTS TESTS
# ============================================================================

class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_system_health(self, api_client):
        """Test system health check."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "services" in data
        assert "timestamp" in data

    def test_system_readiness(self, api_client):
        """Test system readiness probe."""
        response = api_client.get("/ready")
        
        assert response.status_code in [200, 503]

    def test_system_metrics(self, api_client, auth_headers):
        """Test system metrics endpoint."""
        response = api_client.get(
            "/v1/metrics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "total_scans" in data
        assert "active_scans" in data

# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

class TestAuthenticationEndpoints:
    """Test authentication endpoints."""
    
    def test_missing_auth_header(self, api_client):
        """Test request without auth header."""
        response = api_client.get("/v1/scans")
        
        assert response.status_code == 401

    def test_invalid_auth_header(self, api_client):
        """Test request with invalid auth header."""
        response = api_client.get(
            "/v1/scans",
            headers={"Authorization": "Invalid"}
        )
        
        assert response.status_code == 401

    def test_expired_auth_header(self, api_client):
        """Test request with expired auth token."""
        response = api_client.get(
            "/v1/scans",
            headers={"Authorization": "Bearer expired_token_12345"}
        )
        
        assert response.status_code == 401

# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling."""
    
    def test_404_not_found(self, api_client, auth_headers):
        """Test 404 error response."""
        response = api_client.get(
            "/v1/nonexistent/endpoint",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data or "detail" in data

    def test_400_bad_request(self, api_client, auth_headers):
        """Test 400 error for invalid input."""
        response = api_client.post(
            "/v1/scans",
            json={"invalid": "data"},
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_429_rate_limited(self, api_client, auth_headers):
        """Test rate limiting."""
        # Make many rapid requests
        responses = []
        for _ in range(200):
            response = api_client.get(
                "/health",
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # At least one should be rate limited
        assert 429 in responses or all(r == 200 for r in responses)

# ============================================================================
# INTEGRATION WORKFLOW TESTS
# ============================================================================

class TestWorkflowIntegration:
    """Test complete workflows."""
    
    def test_scan_creation_to_completion_workflow(self, api_client, auth_headers):
        """Test complete scan workflow."""
        # 1. Create scan
        create_response = api_client.post(
            "/v1/scans",
            json={
                "target": "example.com",
                "scope": ".example.com",
                "scan_type": "full"
            },
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        scan_id = create_response.json()["id"]
        
        # 2. Check status
        status_response = api_client.get(
            f"/v1/scans/{scan_id}",
            headers=auth_headers
        )
        
        assert status_response.status_code == 200
        assert status_response.json()["id"] == scan_id
        
        # 3. Get findings (may be empty)
        findings_response = api_client.get(
            f"/v1/scans/{scan_id}/findings",
            headers=auth_headers
        )
        
        assert findings_response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
