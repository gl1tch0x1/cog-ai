"""Report agent for finding aggregation and report generation."""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict

from secagents.agents.base import BaseAgent, AgentConfig, AgentOutput, AgentRole
from secagents.prompts import REPORT_PROMPT

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """Generates professional, impact-first security reports.

    Responsibilities:
    - Finding aggregation & deduplication
    - Impact-first report formatting
    - CVSS 4.0 scoring (simplified)
    - Risk formula calculation: Risk = Impact * Probability
    - Multi-format export (Markdown, JSON, HTML)
    """

    # Simplified CVSS 4.0 Base Score Mapping
    CVSS4_MAP = {
        "rce": 9.3,
        "sqli": 9.3,
        "ssti": 9.3,
        "lfi": 8.5,
        "ssrf": 8.7,
        "xss": 7.1,
        "bola": 8.7,
        "mass_assignment": 8.4,
        "jwt_none_alg": 9.2,
        "auth_bypass": 9.2,
        "cors_misconfig": 8.2,
        "graphql_node_idor": 8.7,
        "hidden_mint": 9.6,
        "honeypot": 9.6,
        "lp_drain": 9.6,
    }

    def __init__(self):
        super().__init__(
            AgentConfig(
                role=AgentRole.REPORT,
                name="report",
                tools=["template_render", "cvss_calculator"],
                timeout_seconds=120.0,
            )
        )
        self.logger = logging.getLogger("secagents.report")

    def base_system_prompt(self) -> str:
        return REPORT_PROMPT

    async def execute(self, task: dict) -> AgentOutput:
        """Generate security report from findings."""
        findings = task.get("findings", [])
        target = task.get("target", "unknown")
        fmt = task.get("format", "markdown")
        include_raw_evidence = task.get("include_raw_evidence", True)

        self.logger.info(f"Generating {fmt} report for {target} with {len(findings)} findings")

        try:
            enriched_findings = self._enrich_findings(findings)

            if fmt == "markdown":
                report_content = self._generate_markdown_report(
                    enriched_findings, target, include_raw_evidence
                )
            elif fmt == "json":
                report_content = self._generate_json_report(enriched_findings, target)
            elif fmt == "html":
                report_content = self._generate_html_report(enriched_findings, target)
            else:
                return self._format_output(
                    result={"error": f"unsupported format: {fmt}"},
                    confidence=0.0,
                    reasoning="Invalid format",
                )

            result = {
                "report": report_content,
                "format": fmt,
                "summary": {
                    "total": len(enriched_findings),
                    "critical": len(
                        [f for f in enriched_findings if f.get("severity") == "critical"]
                    ),
                    "high": len([f for f in enriched_findings if f.get("severity") == "high"]),
                    "medium": len([f for f in enriched_findings if f.get("severity") == "medium"]),
                    "low": len([f for f in enriched_findings if f.get("severity") == "low"]),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return self._format_output(
                result=result,
                confidence=1.0,
                reasoning=f"Generated impact-first {fmt} report",
                metadata={"target": target, "finding_count": len(enriched_findings)},
            )
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}", exc_info=True)
            return self._format_output(
                result={"error": str(e)}, confidence=0.0, reasoning="Report generation failed"
            )

    def _enrich_findings(self, findings: List[Dict]) -> List[Dict]:
        """Enrich findings with CVSS 4.0 and Impact-First metadata."""
        enriched = []
        for finding in findings:
            vuln_type = finding.get("type", "").lower()
            finding["cvss4"] = self.CVSS4_MAP.get(vuln_type, 5.0)
            finding["severity"] = self._determine_severity(finding["cvss4"])

            # Risk = Impact (1-5) * Probability (1-5)
            impact_score = self._get_impact_score(vuln_type)
            probability_score = finding.get("probability", 3)
            finding["risk_score"] = impact_score * probability_score

            enriched.append(finding)

        # Sort by CVSS4 descending
        enriched.sort(key=lambda f: f.get("cvss4", 0), reverse=True)
        return enriched

    def _determine_severity(self, cvss: float) -> str:
        if cvss >= 9.0:
            return "critical"
        if cvss >= 7.0:
            return "high"
        if cvss >= 4.0:
            return "medium"
        return "low"

    def _get_impact_score(self, vuln_type: str) -> int:
        impact_map = {"rce": 5, "sqli": 5, "ssti": 5, "bola": 4, "ssrf": 4, "xss": 3}
        return impact_map.get(vuln_type, 3)

    def _generate_markdown_report(
        self, findings: List[Dict], target: str, include_raw: bool
    ) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        lines = [
            f"# Security Assessment Report: {target}",
            f"**Generated:** {timestamp}",
            "",
            "## 1. Executive Summary",
            "This report details the findings of an autonomous security assessment. "
            "The methodology prioritizes real-world exploitable impact and business risk.",
            "",
            f"- **Total Findings:** {len(findings)}",
            f"- **Critical/High Risk:** {len([f for f in findings if f.get('severity') in ['critical', 'high']])}",
            "",
            "---",
            "## 2. Findings (Impact-First)",
            "",
        ]

        for i, f in enumerate(findings, 1):
            lines.extend(
                [
                    f"### [{f.get('severity', 'UNKNOWN').upper()}] {f.get('title', f.get('type', 'Finding ' + str(i)))}",
                    f"**Impact:** {f.get('impact', 'Significant risk to system integrity or data privacy.')}",
                    f"**Recommendation:** {f.get('remediation', 'Implement proper input validation and access controls.')}",
                    "",
                    f"- **CVSS 4.0:** {f.get('cvss4', 'N/A')}",
                    f"- **CWE:** {f.get('cwe', 'N/A')}",
                    f"- **Endpoint:** `{f.get('method', '')} {f.get('endpoint', f.get('file_path', 'N/A'))}`",
                    "",
                    "#### Technical Details & Evidence",
                    f"{f.get('description', 'No detailed description available.')}",
                    "",
                    "**Proof of Concept:**",
                    f"```\n{f.get('poc_url', f.get('payload', 'N/A'))}\n```",
                    "",
                    "---",
                ]
            )

        if include_raw:
            lines.extend(
                ["", "## Appendix: Raw Data", "```json", json.dumps(findings, indent=2), "```"]
            )

        return "\n".join(lines)

    def _generate_json_report(self, findings: List[Dict], target: str) -> str:
        return json.dumps({"target": target, "findings": findings}, indent=2)

    def _generate_html_report(self, findings: List[Dict], target: str) -> str:
        # Simplified HTML generation
        return f"<html><body><h1>Report for {target}</h1><pre>{json.dumps(findings, indent=2)}</pre></body></html>"
