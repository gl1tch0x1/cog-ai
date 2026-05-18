"""Web security agent for vulnerability scanning."""

import asyncio
import logging
import re
from typing import Optional

from secagents.agents.base import BaseAgent, AgentConfig, AgentOutput, AgentRole
from secagents.prompts import WEB_SECURITY_PROMPT

logger = logging.getLogger(__name__)


class WebSecurityAgent(BaseAgent):
    """Tests web vulnerabilities: XSS, SQLi, SSRF, LFI, RCE, SSTI, etc.
    
    Responsibilities:
    - Generate context-aware payloads
    - Test multiple vulnerability types
    - Validate findings with response analysis
    - Minimize false positives
    """

    # Vulnerability detection signatures
    VULN_SIGNATURES = {
        "sqli": {
            "patterns": [
                r"SQL syntax error",
                r"mysql_fetch_array",
                r"Warning.*MySQL",
                r"PostgreSQL.*error",
                r"Oracle error",
                r"ODBC.*Driver",
            ],
            "payloads": ["' OR '1'='1", "' UNION SELECT NULL--", "';DROP TABLE users--"],
        },
        "xss": {
            "patterns": [
                r"<img\s+src=x\s+onerror=alert",
                r"<svg.*onload=alert",
                r"<iframe.*src=javascript",
                r"<body.*onload=alert",
            ],
            "payloads": [
                "<img src=x onerror=alert(1)>",
                "<svg onload=alert(1)>",
                "<iframe src=javascript:alert(1)>",
            ],
        },
        "ssti": {
            "patterns": [
                r"\{\{.*\}\}",
                r"\$\{.*\}",
                r"\[%.*%\]",
                r"49",  # 7*7 result
                r"72",  # 8*9 result
            ],
            "payloads": [
                "{{7*7}}",
                "${7*7}",
                "[%7*7%]",
            ],
        },
        "lfi": {
            "patterns": [
                r"root:.*:0:0:",
                r"bin/bash",
                r"etc/passwd",
            ],
            "payloads": [
                "../../../etc/passwd",
                "....//....//....//etc/passwd",
                "%2e%2e%2fetc%2fpasswd",
            ],
        },
        "ssrf": {
            "patterns": [
                r"ami-id",
                r"instance-id",
                r"iam/security-credentials",
                r"metadata",
            ],
            "payloads": [
                "http://169.254.169.254/latest/meta-data/",
                "http://localhost:9000/",
                "http://127.0.0.1:8080/admin",
            ],
        },
        "rce": {
            "patterns": [
                r"uid=",
                r"gid=",
                r"groups=",
                r"command not found",
            ],
            "payloads": [
                "; id #",
                "| whoami",
                "`whoami`",
                "$(whoami)",
            ],
        },
    }

    def __init__(self):
        super().__init__(AgentConfig(
            role=AgentRole.WEB_SECURITY,
            name="web_security",
            tools=["http_request", "payload_generate", "response_analyze"],
            timeout_seconds=300.0,
        ))
        self.logger = logging.getLogger("secagents.web_security")

    def system_prompt(self) -> str:
        """Return the web security agent's system prompt."""
        return WEB_SECURITY_PROMPT

    async def execute(self, task: dict) -> AgentOutput:
        """Execute web vulnerability scanning."""
        target = task.get("target", "")
        endpoints = task.get("endpoints", [])
        vuln_types = task.get("vuln_types", list(self.VULN_SIGNATURES.keys()))

        if not endpoints:
            self.logger.error("No endpoints specified")
            return self._format_output(
                result={"error": "endpoints required"},
                confidence=0.0,
                reasoning="No endpoints to test",
            )

        self.logger.info(f"Testing {len(endpoints)} endpoints for {len(vuln_types)} vuln types")

        try:
            findings = await self._test_endpoints(endpoints, vuln_types, target)

            confidence = self._calculate_confidence(
                evidence_count=len(findings),
                max_evidence=20,
                base_confidence=0.6,
            )

            result = {
                "findings": findings,
                "endpoints_tested": len(endpoints),
                "vuln_types_tested": len(vuln_types),
                "total_payloads_sent": len(endpoints) * len(vuln_types),
            }

            self.logger.info(f"Found {len(findings)} potential vulnerabilities")

            return self._format_output(
                result=result,
                confidence=confidence,
                reasoning=f"Tested {len(endpoints)} endpoints for {len(vuln_types)} vuln types",
                metadata={
                    "target": target,
                    "endpoint_count": len(endpoints),
                    "vuln_type_count": len(vuln_types),
                },
            )
        except Exception as e:
            self.logger.error(f"Web security scan failed: {str(e)}", exc_info=True)
            return self._format_output(
                result={"error": str(e)},
                confidence=0.0,
                reasoning="Scan execution failed",
            )

    async def _test_endpoints(self, endpoints: list[str], vuln_types: list[str], target: str) -> list[dict]:
        """Test multiple endpoints for vulnerabilities.
        
        Args:
            endpoints: List of endpoints to test
            vuln_types: Vulnerability types to check
            target: Target base URL
            
        Returns:
            List of findings
        """
        findings = []

        tasks = []
        for endpoint in endpoints:
            for vuln_type in vuln_types:
                tasks.append(self._test(endpoint, vuln_type, target))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(f"Test failed: {str(result)}")
            elif isinstance(result, dict) and result:
                findings.append(result)

        return findings

    async def _test(self, endpoint: str, vuln_type: str, target: str) -> Optional[dict]:
        """Test a single endpoint for a vulnerability type.
        
        Args:
            endpoint: Endpoint path
            vuln_type: Vulnerability type
            target: Target base URL
            
        Returns:
            Finding if vulnerability detected
        """
        if vuln_type not in self.VULN_SIGNATURES:
            return None

        sig = self.VULN_SIGNATURES[vuln_type]
        payloads = sig.get("payloads", [])
        patterns = sig.get("patterns", [])

        for payload in payloads:
            response = await self._send_payload(endpoint, payload, target)
            
            if response and self._check_response(response, patterns):
                return {
                    "type": vuln_type,
                    "endpoint": endpoint,
                    "payload": payload,
                    "poc_url": f"{target}{endpoint}?param={payload}",
                    "confidence": 0.8,
                    "severity": self._get_severity(vuln_type),
                    "cwe": self._get_cwe(vuln_type),
                }

        return None

    async def _send_payload(self, endpoint: str, payload: str, target: str) -> Optional[str]:
        """Send payload to endpoint and get response.
        
        Args:
            endpoint: Target endpoint
            payload: Payload to send
            target: Base URL
            
        Returns:
            Response body
        """
        try:
            # Simulate HTTP request
            url = f"{target}{endpoint}?test={payload}"
            self.logger.debug(f"Testing: {url}")
            
            # In production, this would make actual HTTP request
            await asyncio.sleep(0.01)  # Simulate network latency
            
            return f"Response from {endpoint} with payload"
        except Exception as e:
            self.logger.error(f"Failed to send payload: {str(e)}")
            return None

    def _check_response(self, response: str, patterns: list[str]) -> bool:
        """Check response for vulnerability patterns.
        
        Args:
            response: Response body
            patterns: Regex patterns to match
            
        Returns:
            True if vulnerability pattern found
        """
        for pattern in patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        return False

    def _get_severity(self, vuln_type: str) -> str:
        """Get severity for vulnerability type.
        
        Args:
            vuln_type: Vulnerability type
            
        Returns:
            Severity level
        """
        severity_map = {
            "rce": "critical",
            "sqli": "critical",
            "ssti": "critical",
            "lfi": "high",
            "ssrf": "high",
            "xss": "high",
        }
        return severity_map.get(vuln_type, "medium")

    def _get_cwe(self, vuln_type: str) -> str:
        """Get CWE ID for vulnerability type.
        
        Args:
            vuln_type: Vulnerability type
            
        Returns:
            CWE ID
        """
        cwe_map = {
            "sqli": "CWE-89",
            "xss": "CWE-79",
            "ssti": "CWE-1336",
            "lfi": "CWE-22",
            "ssrf": "CWE-918",
            "rce": "CWE-78",
        }
        return cwe_map.get(vuln_type, "CWE-20")
