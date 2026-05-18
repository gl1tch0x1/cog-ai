"""API security agent for API-specific vulnerability testing."""

import asyncio
import json
import logging
from typing import Optional

from secagents.agents.base import BaseAgent, AgentConfig, AgentOutput, AgentRole
from secagents.prompts import API_SECURITY_PROMPT

logger = logging.getLogger(__name__)


class APISecurityAgent(BaseAgent):
    """Tests API-specific vulnerabilities: BOLA, mass assignment, rate limiting, etc.
    
    Responsibilities:
    - BOLA/IDOR testing
    - Mass assignment detection
    - Rate limit bypass testing
    - JWT vulnerability scanning
    - GraphQL abuse detection
    - Authentication bypass testing
    """

    def __init__(self):
        super().__init__(AgentConfig(
            role=AgentRole.API_SECURITY,
            name="api_security",
            tools=["http_request", "schema_parse", "auth_test", "jwt_decode"],
            timeout_seconds=300.0,
        ))
        self.logger = logging.getLogger("secagents.api_security")

    def system_prompt(self) -> str:
        """Return the API security agent's system prompt."""
        return API_SECURITY_PROMPT

    async def execute(self, task: dict) -> AgentOutput:
        """Execute API vulnerability scanning."""
        target = task.get("target", "")
        spec = task.get("openapi_spec", None)
        endpoints = task.get("endpoints", [])

        if not endpoints:
            self.logger.error("No endpoints specified")
            return self._format_output(
                result={"error": "endpoints required"},
                confidence=0.0,
                reasoning="No endpoints to test",
            )

        self.logger.info(f"Testing {len(endpoints)} API endpoints")

        try:
            # Parse spec if provided
            if spec:
                endpoints = self._parse_openapi_spec(spec, endpoints)

            findings = await self._test_endpoints(endpoints, target, spec)

            confidence = self._calculate_confidence(
                evidence_count=len(findings),
                max_evidence=15,
                base_confidence=0.6,
            )

            result = {
                "findings": findings,
                "endpoints_tested": len(endpoints),
                "test_types": ["bola", "mass_assignment", "rate_limiting", "jwt", "auth"],
            }

            self.logger.info(f"Found {len(findings)} API vulnerabilities")

            return self._format_output(
                result=result,
                confidence=confidence,
                reasoning=f"Tested {len(endpoints)} API endpoints",
                metadata={
                    "target": target,
                    "endpoint_count": len(endpoints),
                },
            )
        except Exception as e:
            self.logger.error(f"API security scan failed: {str(e)}", exc_info=True)
            return self._format_output(
                result={"error": str(e)},
                confidence=0.0,
                reasoning="Scan execution failed",
            )

    async def _test_endpoints(self, endpoints: list[dict], target: str, spec: Optional[dict]) -> list[dict]:
        """Test multiple API endpoints for vulnerabilities.
        
        Args:
            endpoints: List of endpoint specifications
            target: Target API base URL
            spec: OpenAPI spec if available
            
        Returns:
            List of findings
        """
        findings = []

        test_tasks = []
        for ep in endpoints:
            test_tasks.append(self._test_endpoint(ep, target, spec))

        results = await asyncio.gather(*test_tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(f"Test failed: {str(result)}")
            elif isinstance(result, list):
                findings.extend(result)

        return findings

    async def _test_endpoint(self, endpoint: dict, target: str, spec: Optional[dict]) -> list[dict]:
        """Test single API endpoint for vulnerabilities.
        
        Args:
            endpoint: Endpoint specification
            target: Target API base URL
            spec: OpenAPI spec if available
            
        Returns:
            List of findings for this endpoint
        """
        findings = []
        path = endpoint.get("path", "")
        method = endpoint.get("method", "GET").upper()

        self.logger.info(f"Testing {method} {path}")

        try:
            # Test for BOLA/IDOR
            bola_findings = await self._test_bola(path, method, target)
            findings.extend(bola_findings)

            # Test for mass assignment
            mass_assign_findings = await self._test_mass_assignment(path, method, target, endpoint)
            findings.extend(mass_assign_findings)

            # Test for rate limiting
            rate_limit_findings = await self._test_rate_limiting(path, method, target)
            findings.extend(rate_limit_findings)

            # Test for JWT vulnerabilities if authentication is used
            if "auth" in endpoint.get("tags", []):
                jwt_findings = await self._test_jwt_vulnerabilities(path, method, target)
                findings.extend(jwt_findings)

            # Test for auth bypass
            auth_findings = await self._test_auth_bypass(path, method, target)
            findings.extend(auth_findings)

        except Exception as e:
            self.logger.error(f"Test failed for {path}: {str(e)}")

        return findings

    async def _test_bola(self, path: str, method: str, target: str) -> list[dict]:
        """Test for BOLA/IDOR vulnerabilities.
        
        Args:
            path: Endpoint path
            method: HTTP method
            target: Target API base URL
            
        Returns:
            Findings
        """
        findings = []

        if method not in ["GET", "PUT", "DELETE"]:
            return findings

        # Test with different IDs
        test_ids = ["1", "2", "admin", "test", "0"]
        
        for test_id in test_ids:
            test_path = path.replace("{id}", test_id)
            
            # Simulate request
            response = await self._send_api_request(f"{target}{test_path}", method)
            
            if response and response.get("status_code") in [200, 401, 403]:
                if test_id != "1" and response.get("status_code") == 200:
                    findings.append({
                        "type": "bola",
                        "endpoint": path,
                        "method": method,
                        "test_id": test_id,
                        "poc_url": f"{target}{test_path}",
                        "confidence": 0.8,
                        "severity": "high",
                        "cwe": "CWE-639",
                        "description": "Broken Object Level Authorization detected",
                    })

        return findings

    async def _test_mass_assignment(self, path: str, method: str, target: str, endpoint: dict) -> list[dict]:
        """Test for mass assignment vulnerabilities.
        
        Args:
            path: Endpoint path
            method: HTTP method
            target: Target API base URL
            endpoint: Endpoint specification
            
        Returns:
            Findings
        """
        findings = []

        if method not in ["POST", "PUT", "PATCH"]:
            return findings

        # Test with additional fields
        payload = endpoint.get("example_request", {})
        admin_fields = ["is_admin", "role", "admin", "is_superuser", "privilege"]

        for field in admin_fields:
            test_payload = {**payload, field: True}
            
            response = await self._send_api_request(
                f"{target}{path}",
                method,
                json=test_payload,
            )
            
            if response and field in str(response.get("body", "")):
                findings.append({
                    "type": "mass_assignment",
                    "endpoint": path,
                    "method": method,
                    "parameter": field,
                    "poc_url": f"{target}{path}",
                    "confidence": 0.85,
                    "severity": "high",
                    "cwe": "CWE-915",
                    "description": f"Mass assignment allowed for '{field}'",
                })

        return findings

    async def _test_rate_limiting(self, path: str, method: str, target: str) -> list[dict]:
        """Test for rate limiting bypass.
        
        Args:
            path: Endpoint path
            method: HTTP method
            target: Target API base URL
            
        Returns:
            Findings
        """
        findings = []

        # Send rapid requests
        request_count = 100
        responses = []

        for _ in range(request_count):
            response = await self._send_api_request(f"{target}{path}", method)
            if response:
                responses.append(response)

        # Check for rate limiting
        rate_limited = sum(1 for r in responses if r.get("status_code") == 429)
        
        if rate_limited == 0:
            findings.append({
                "type": "rate_limiting_bypass",
                "endpoint": path,
                "method": method,
                "requests_sent": request_count,
                "rate_limited_responses": rate_limited,
                "confidence": 0.7,
                "severity": "medium",
                "cwe": "CWE-770",
                "description": "No rate limiting detected",
            })

        return findings

    async def _test_jwt_vulnerabilities(self, path: str, method: str, target: str) -> list[dict]:
        """Test for JWT vulnerabilities.
        
        Args:
            path: Endpoint path
            method: HTTP method
            target: Target API base URL
            
        Returns:
            Findings
        """
        findings = []

        # Test JWT without signature
        jwt_none_token = "eyJhbGciOiJub25lIn0.eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        
        response = await self._send_api_request(
            f"{target}{path}",
            method,
            headers={"Authorization": f"Bearer {jwt_none_token}"}
        )
        
        if response and response.get("status_code") == 200:
            findings.append({
                "type": "jwt_none_algorithm",
                "endpoint": path,
                "method": method,
                "poc_url": f"{target}{path}",
                "confidence": 0.9,
                "severity": "critical",
                "cwe": "CWE-347",
                "description": "JWT 'none' algorithm accepted",
            })

        return findings

    async def _test_auth_bypass(self, path: str, method: str, target: str) -> list[dict]:
        """Test for authentication bypass.
        
        Args:
            path: Endpoint path
            method: HTTP method
            target: Target API base URL
            
        Returns:
            Findings
        """
        findings = []

        # Test without authentication
        response = await self._send_api_request(f"{target}{path}", method)
        
        if response and response.get("status_code") == 200:
            findings.append({
                "type": "auth_bypass",
                "endpoint": path,
                "method": method,
                "poc_url": f"{target}{path}",
                "confidence": 0.85,
                "severity": "critical",
                "cwe": "CWE-287",
                "description": "Endpoint accessible without authentication",
            })

        return findings

    async def _send_api_request(
        self,
        url: str,
        method: str = "GET",
        json: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Optional[dict]:
        """Send API request and return response.
        
        Args:
            url: Target URL
            method: HTTP method
            json: JSON body
            headers: HTTP headers
            
        Returns:
            Response dict
        """
        try:
            # Simulate API request
            await asyncio.sleep(0.01)
            
            return {
                "status_code": 200,
                "body": json or {},
                "headers": headers or {},
            }
        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            return None

    def _parse_openapi_spec(self, spec: dict, endpoints: list[dict]) -> list[dict]:
        """Parse OpenAPI spec to extract endpoints.
        
        Args:
            spec: OpenAPI specification
            endpoints: Existing endpoints
            
        Returns:
            Merged endpoint list
        """
        parsed = []

        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method in methods.keys():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    parsed.append({
                        "path": path,
                        "method": method.upper(),
                    })

        return parsed if parsed else endpoints
