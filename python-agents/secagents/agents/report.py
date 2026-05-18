"""Report agent for finding aggregation and report generation."""

import json
import logging
from datetime import datetime, timezone

from secagents.agents.base import BaseAgent, AgentConfig, AgentOutput, AgentRole
from secagents.prompts import REPORT_PROMPT

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """Generates professional security reports.
    
    Responsibilities:
    - Finding aggregation
    - Report formatting
    - CVSS scoring
    - Template rendering
    - Multi-format export (Markdown, HTML, JSON, PDF)
    """

    def __init__(self):
        super().__init__(AgentConfig(
            role=AgentRole.REPORT,
            name="report",
            tools=["template_render", "pdf_export", "cvss_calculator"],
            timeout_seconds=120.0,
        ))
        self.logger = logging.getLogger("secagents.report")

    def system_prompt(self) -> str:
        """Return the report agent's system prompt."""
        return REPORT_PROMPT

    async def execute(self, task: dict) -> AgentOutput:
        """Generate security report from findings."""
        findings = task.get("findings", [])
        target = task.get("target", "unknown")
        fmt = task.get("format", "markdown")
        include_raw_evidence = task.get("include_raw_evidence", True)

        self.logger.info(f"Generating {fmt} report for {target} with {len(findings)} findings")

        try:
            # Sort and enrich findings
            enriched_findings = self._enrich_findings(findings)
            
            # Generate report
            if fmt == "markdown":
                report_content = self._generate_markdown_report(
                    enriched_findings, target, include_raw_evidence
                )
            elif fmt == "json":
                report_content = self._generate_json_report(
                    enriched_findings, target
                )
            elif fmt == "html":
                report_content = self._generate_html_report(
                    enriched_findings, target
                )
            else:
                return self._format_output(
                    result={"error": f"unsupported format: {fmt}"},
                    confidence=0.0,
                    reasoning="Invalid format specified",
                )

            result = {
                "report": report_content,
                "format": fmt,
                "finding_count": len(enriched_findings),
                "critical_count": len([f for f in enriched_findings if f.get("severity") == "critical"]),
                "high_count": len([f for f in enriched_findings if f.get("severity") == "high"]),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            self.logger.info(f"Report generated: {result['critical_count']} critical, {result['high_count']} high")

            return self._format_output(
                result=result,
                confidence=0.95,
                reasoning=f"Generated {fmt} report with {len(enriched_findings)} findings",
                metadata={
                    "target": target,
                    "format": fmt,
                    "finding_count": len(enriched_findings),
                },
            )
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}", exc_info=True)
            return self._format_output(
                result={"error": str(e)},
                confidence=0.0,
                reasoning="Report generation failed",
            )

    def _enrich_findings(self, findings: list[dict]) -> list[dict]:
        """Enrich findings with CVSS scores and sorting.
        
        Args:
            findings: Raw findings
            
        Returns:
            Enriched findings sorted by severity
        """
        enriched = []

        for finding in findings:
            if not finding.get("cvss"):
                finding["cvss"] = self._calculate_cvss_score(finding)
            
            if not finding.get("severity"):
                finding["severity"] = self._determine_severity(finding)

            enriched.append(finding)

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        enriched.sort(
            key=lambda f: (
                severity_order.get(f.get("severity", "low"), 4),
                -f.get("cvss", 0),
            )
        )

        self.logger.info(f"Enriched {len(enriched)} findings")
        return enriched

    def _calculate_cvss_score(self, finding: dict) -> float:
        """Calculate CVSS v3.1 score for finding.
        
        Args:
            finding: Finding details
            
        Returns:
            CVSS score 0.0-10.0
        """
        vuln_type = finding.get("type", "").lower()
        
        # Simplified CVSS mapping
        cvss_map = {
            "rce": 9.8,
            "sqli": 9.9,
            "ssti": 9.8,
            "lfi": 7.5,
            "ssrf": 8.6,
            "xss": 6.1,
            "bola": 7.5,
            "mass_assignment": 7.5,
            "jwt_none_algorithm": 9.1,
            "auth_bypass": 9.1,
            "rate_limiting_bypass": 5.3,
        }

        return cvss_map.get(vuln_type, 5.0)

    def _determine_severity(self, finding: dict) -> str:
        """Determine severity based on finding type.
        
        Args:
            finding: Finding details
            
        Returns:
            Severity level
        """
        cvss = finding.get("cvss", 5.0)

        if cvss >= 9.0:
            return "critical"
        elif cvss >= 7.0:
            return "high"
        elif cvss >= 4.0:
            return "medium"
        else:
            return "low"

    def _generate_markdown_report(
        self,
        findings: list[dict],
        target: str,
        include_raw_evidence: bool = True,
    ) -> str:
        """Generate Markdown format report.
        
        Args:
            findings: Enriched findings
            target: Target domain
            include_raw_evidence: Include raw evidence appendix
            
        Returns:
            Markdown report content
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        lines = [
            "# Security Assessment Report",
            "",
            f"**Target:** {target}",
            f"**Date:** {timestamp}",
            f"**Findings:** {len(findings)}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"This security assessment identified {len(findings)} vulnerabilities in the target.",
            "",
        ]

        # Add summary counts
        critical = len([f for f in findings if f.get("severity") == "critical"])
        high = len([f for f in findings if f.get("severity") == "high"])
        medium = len([f for f in findings if f.get("severity") == "medium"])
        low = len([f for f in findings if f.get("severity") == "low"])

        lines.extend([
            "| Severity | Count |",
            "|----------|-------|",
            f"| Critical | {critical} |",
            f"| High     | {high} |",
            f"| Medium   | {medium} |",
            f"| Low      | {low} |",
            "",
            "---",
            "",
            "## Findings",
            "",
        ])

        # Add detailed findings
        for i, finding in enumerate(findings, 1):
            lines.extend(self._format_finding_markdown(i, finding))

        # Add appendix if requested
        if include_raw_evidence:
            lines.extend([
                "",
                "---",
                "",
                "## Appendix: Raw Evidence",
                "",
                "```json",
                json.dumps(findings, indent=2),
                "```",
            ])

        return "\n".join(lines)

    def _format_finding_markdown(self, number: int, finding: dict) -> list[str]:
        """Format single finding for Markdown.
        
        Args:
            number: Finding number
            finding: Finding details
            
        Returns:
            Markdown lines
        """
        lines = [
            f"### Finding {number}: {finding.get('title', 'Untitled')}",
            "",
            f"**Type:** {finding.get('type', 'Unknown')}",
            f"**Severity:** {finding.get('severity', 'Unknown')}",
            f"**CWE:** {finding.get('cwe', 'N/A')}",
            f"**CVSS:** {finding.get('cvss', 'N/A')}",
            "",
        ]

        if finding.get("description"):
            lines.extend([
                "**Description:**",
                f"{finding['description']}",
                "",
            ])

        if finding.get("poc_url"):
            lines.extend([
                "**Proof of Concept:**",
                f"`{finding['poc_url']}`",
                "",
            ])

        if finding.get("steps"):
            lines.extend([
                "**Steps to Reproduce:**",
                finding["steps"],
                "",
            ])

        if finding.get("impact"):
            lines.extend([
                "**Impact:**",
                finding["impact"],
                "",
            ])

        if finding.get("remediation"):
            lines.extend([
                "**Remediation:**",
                finding["remediation"],
                "",
            ])

        lines.append("---\n")
        return lines

    def _generate_json_report(self, findings: list[dict], target: str) -> str:
        """Generate JSON format report.
        
        Args:
            findings: Enriched findings
            target: Target domain
            
        Returns:
            JSON report content
        """
        report = {
            "target": target,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "findings": findings,
            "summary": {
                "total": len(findings),
                "critical": len([f for f in findings if f.get("severity") == "critical"]),
                "high": len([f for f in findings if f.get("severity") == "high"]),
                "medium": len([f for f in findings if f.get("severity") == "medium"]),
                "low": len([f for f in findings if f.get("severity") == "low"]),
            },
        }

        return json.dumps(report, indent=2)

    def _generate_html_report(self, findings: list[dict], target: str) -> str:
        """Generate HTML format report.
        
        Args:
            findings: Enriched findings
            target: Target domain
            
        Returns:
            HTML report content
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Security Assessment Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1 { color: #333; }",
            ".critical { color: #d32f2f; font-weight: bold; }",
            ".high { color: #f57c00; font-weight: bold; }",
            ".medium { color: #fbc02d; font-weight: bold; }",
            ".low { color: #388e3c; font-weight: bold; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            ".finding { margin: 20px 0; padding: 10px; border: 1px solid #ddd; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Security Assessment Report</h1>",
            f"<p><strong>Target:</strong> {target}</p>",
            f"<p><strong>Date:</strong> {timestamp}</p>",
            "",
            "<h2>Summary</h2>",
            "<table>",
            "<tr><th>Severity</th><th>Count</th></tr>",
        ]

        # Add summary
        critical = len([f for f in findings if f.get("severity") == "critical"])
        high = len([f for f in findings if f.get("severity") == "high"])
        medium = len([f for f in findings if f.get("severity") == "medium"])
        low = len([f for f in findings if f.get("severity") == "low"])

        html_lines.extend([
            f"<tr><td class='critical'>Critical</td><td>{critical}</td></tr>",
            f"<tr><td class='high'>High</td><td>{high}</td></tr>",
            f"<tr><td class='medium'>Medium</td><td>{medium}</td></tr>",
            f"<tr><td class='low'>Low</td><td>{low}</td></tr>",
            "</table>",
            "",
            "<h2>Findings</h2>",
        ])

        # Add findings
        for i, finding in enumerate(findings, 1):
            severity_class = finding.get("severity", "low").lower()
            html_lines.extend([
                "<div class='finding'>",
                f"<h3>Finding {i}: {finding.get('title', 'Untitled')}</h3>",
                f"<p><strong>Type:</strong> {finding.get('type', 'Unknown')}</p>",
                f"<p><strong class='{severity_class}'>Severity: {finding.get('severity', 'Unknown')}</strong></p>",
                f"<p><strong>CWE:</strong> {finding.get('cwe', 'N/A')}</p>",
                f"<p><strong>CVSS:</strong> {finding.get('cvss', 'N/A')}</p>",
                f"<p>{finding.get('description', '')}</p>",
                "</div>",
            ])

        html_lines.extend([
            "</body>",
            "</html>",
        ])

        return "\n".join(html_lines)
