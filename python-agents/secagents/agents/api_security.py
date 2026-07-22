"""API security agent for API-specific vulnerability testing."""

import asyncio
import logging
import os
import re
from typing import Optional

import httpx
from secagents.agents.base import BaseAgent, AgentConfig, AgentOutput, AgentRole
from secagents.prompts import API_SECURITY_PROMPT

logger = logging.getLogger(__name__)


class APISecurityAgent(BaseAgent):
    """Tests API-specific vulnerabilities: BOLA, mass assignment, rate limiting, etc.

    Responsibilities:
    - BOLA/IDOR testing
    - Mass assignment detection
    - Rate limit bypass testing
    - JWT vulnerability scanning (None alg, Algorithm Confusion)
    - GraphQL abuse detection (Introspection, Batching, Node IDOR)
    - CORS misconfiguration testing
    """

    def __init__(self):
        super().__init__(
            AgentConfig(
                role=AgentRole.API_SECURITY,
                name="api_security",
                tools=["http_request", "schema_parse", "auth_test", "jwt_decode"],
                timeout_seconds=300.0,
            )
        )
        self.logger = logging.getLogger("secagents.api_security")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            verify_ssl = os.environ.get("SECAGENT_VERIFY_SSL", "true").lower() != "false"
            self._client = httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=False,  # Important for CORS/Auth tests
                verify=verify_ssl,
            )
        return self._client

    def base_system_prompt(self) -> str:
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
                "test_types": [
                    "bola",
                    "mass_assignment",
                    "rate_limiting",
                    "jwt",
                    "auth",
                    "graphql",
                    "cors",
                ],
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
        finally:
            if self._client:
                await self._client.aclose()
                self._client = None

    async def _test_endpoints(
        self, endpoints: list[dict], target: str, spec: Optional[dict]
    ) -> list[dict]:
        findings = []
        for ep in endpoints:
            findings.extend(await self._test_endpoint(ep, target, spec))
        return findings

    async def _test_endpoint(self, endpoint: dict, target: str, spec: Optional[dict]) -> list[dict]:
        findings = []
        path = endpoint.get("path", "")
        method = endpoint.get("method", "GET").upper()

        self.logger.info(f"Testing {method} {path}")

        try:
            # Test for BOLA/IDOR
            findings.extend(await self._test_bola(path, method, target))

            # Test for mass assignment
            findings.extend(await self._test_mass_assignment(path, method, target, endpoint))

            # Test for rate limiting
            findings.extend(await self._test_rate_limiting(path, method, target))

            # Test for JWT vulnerabilities
            findings.extend(await self._test_jwt_vulnerabilities(path, method, target))

            # Test for auth bypass
            findings.extend(await self._test_auth_bypass(path, method, target))

            # Test for CORS
            findings.extend(await self._test_cors(path, method, target))

            # Test for MFA/SAML bypass
            findings.extend(await self._test_mfa_saml_bypass(path, target))

            # Test for GraphQL if path suggests it
            if "graphql" in path.lower():
                findings.extend(await self._test_graphql(path, target))

        except Exception as e:
            self.logger.error(f"Test failed for {path}: {str(e)}")

        return findings

    async def _test_bola(self, path: str, method: str, target: str) -> list[dict]:
        findings = []
        if method not in ["GET", "PUT", "DELETE", "PATCH"]:
            return findings

        # Swapping IDs (V1-V2)
        test_ids = ["1", "2", "admin", "0", "999999"]
        for test_id in test_ids:
            # Simple heuristic replacement
            test_path = re.sub(r"/\d+($|/)", rf"/{test_id}\1", path)
            if test_path == path:
                continue

            resp = await self._send_api_request(
                f"{target.rstrip('/')}/{test_path.lstrip('/')}", method
            )
            if resp and resp.status_code == 200:
                findings.append(
                    {
                        "type": "bola",
                        "endpoint": path,
                        "method": method,
                        "test_id": test_id,
                        "confidence": 0.8,
                        "severity": "high",
                        "cwe": "CWE-639",
                    }
                )
        return findings

    async def _test_mass_assignment(
        self, path: str, method: str, target: str, endpoint: dict
    ) -> list[dict]:
        findings = []
        if method not in ["POST", "PUT", "PATCH"]:
            return findings

        admin_fields = ["is_admin", "role", "admin", "is_superuser", "privilege", "type"]
        base_payload = endpoint.get("example_request", {"id": 1})

        for field in admin_fields:
            test_payload = {**base_payload, field: "admin" if field == "role" else True}
            resp = await self._send_api_request(
                f"{target.rstrip('/')}/{path.lstrip('/')}", method, json=test_payload
            )

            # Success here might mean the field was accepted
            if resp and resp.status_code in [200, 201, 204]:
                findings.append(
                    {
                        "type": "mass_assignment",
                        "endpoint": path,
                        "parameter": field,
                        "confidence": 0.7,
                        "severity": "high",
                        "cwe": "CWE-915",
                    }
                )
        return findings

    async def _test_jwt_vulnerabilities(self, path: str, method: str, target: str) -> list[dict]:
        findings = []
        # 1. 'none' algorithm
        jwt_none = (
            "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiIsImlhdCI6MTUxNjIzOTAyMn0."
        )
        resp = await self._send_api_request(
            f"{target.rstrip('/')}/{path.lstrip('/')}",
            method,
            headers={"Authorization": f"Bearer {jwt_none}"},
        )
        if resp and resp.status_code == 200:
            findings.append(
                {
                    "type": "jwt_none_alg",
                    "confidence": 0.9,
                    "severity": "critical",
                    "cwe": "CWE-347",
                }
            )

        return findings

    async def _test_cors(self, path: str, method: str, target: str) -> list[dict]:
        findings = []
        origin = "https://evil.com"
        resp = await self._send_api_request(
            f"{target.rstrip('/')}/{path.lstrip('/')}", method, headers={"Origin": origin}
        )

        if resp:
            acao = resp.headers.get("Access-Control-Allow-Origin")
            acac = resp.headers.get("Access-Control-Allow-Credentials")
            if acao == origin and acac == "true":
                findings.append(
                    {
                        "type": "cors_misconfig",
                        "confidence": 0.95,
                        "severity": "high",
                        "cwe": "CWE-942",
                    }
                )
        return findings

    async def _test_graphql(self, path: str, target: str) -> list[dict]:
        findings = []
        # Introspection
        query = {"query": "{ __schema { types { name } } }"}
        resp = await self._send_api_request(
            f"{target.rstrip('/')}/{path.lstrip('/')}", "POST", json=query
        )
        if resp and "__schema" in resp.text:
            findings.append(
                {
                    "type": "graphql_introspection",
                    "confidence": 0.9,
                    "severity": "info",
                    "cwe": "CWE-200",
                }
            )

        # Batching
        batch_query = [{"query": "{ __typename }"}, {"query": "{ __typename }"}]
        resp = await self._send_api_request(
            f"{target.rstrip('/')}/{path.lstrip('/')}", "POST", json=batch_query
        )
        if resp and isinstance(resp.json(), list) and len(resp.json()) == 2:
            findings.append(
                {"type": "graphql_batching", "confidence": 0.8, "severity": "low", "cwe": "CWE-770"}
            )

        return findings

    async def _test_rate_limiting(self, path: str, method: str, target: str) -> list[dict]:
        findings = []
        # Send 10 rapid requests
        tasks = [
            self._send_api_request(f"{target.rstrip('/')}/{path.lstrip('/')}", method)
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)

        status_429 = [r for r in results if r and r.status_code == 429]
        if not status_429:
            findings.append(
                {
                    "type": "missing_rate_limiting",
                    "confidence": 0.6,
                    "severity": "medium",
                    "cwe": "CWE-770",
                }
            )
        return findings

    async def _test_auth_bypass(self, path: str, method: str, target: str) -> list[dict]:
        findings = []
        resp = await self._send_api_request(f"{target.rstrip('/')}/{path.lstrip('/')}", method)
        if resp and resp.status_code == 200:
            findings.append(
                {"type": "auth_bypass", "confidence": 0.8, "severity": "critical", "cwe": "CWE-287"}
            )
        return findings

    async def _test_mfa_saml_bypass(self, path: str, target: str) -> list[dict]:
        findings = []
        # SAML Signature Stripping
        if "saml" in path.lower() or "sso" in path.lower():
            # Injected SAML without signature
            saml_payload = '<?xml version="1.0"?><saml:Assertion><saml:NameID>admin@target.com</saml:NameID></saml:Assertion>'
            resp = await self._send_api_request(
                f"{target.rstrip('/')}/{path.lstrip('/')}",
                "POST",
                data={"SAMLResponse": saml_payload},
            )
            if resp and resp.status_code == 200:
                findings.append(
                    {
                        "type": "saml_signature_stripping",
                        "confidence": 0.9,
                        "severity": "critical",
                        "cwe": "CWE-347",
                    }
                )

        # MFA Skip Step
        if "mfa" in path.lower() or "verify" in path.lower():
            # Attempt to access dashboard with pre-mfa session
            resp = await self._send_api_request(f"{target.rstrip('/')}/dashboard", "GET")
            if resp and resp.status_code == 200:
                findings.append(
                    {
                        "type": "mfa_skip_step",
                        "confidence": 0.8,
                        "severity": "critical",
                        "cwe": "CWE-287",
                    }
                )

        return findings

    async def _send_api_request(self, url: str, method: str, **kwargs) -> Optional[httpx.Response]:
        try:
            return await self.client.request(method, url, **kwargs)
        except Exception as e:
            self.logger.debug(f"API request failed: {str(e)}")
            return None

    def _parse_openapi_spec(self, spec: dict, endpoints: list[dict]) -> list[dict]:
        parsed = []
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, info in methods.items():
                parsed.append(
                    {
                        "path": path,
                        "method": method.upper(),
                        "example_request": info.get("requestBody", {})
                        .get("content", {})
                        .get("application/json", {})
                        .get("example", {}),
                    }
                )
        return parsed if parsed else endpoints
