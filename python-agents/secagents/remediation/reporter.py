"""Executive and technical reports in JSON, Markdown, HTML."""

from __future__ import annotations

import html
import json
import time
from pathlib import Path


SEVERITY_SCORE = {"critical": 10, "high": 7, "medium": 5, "low": 2, "info": 0}


class ReportGenerator:
    def __init__(self, output_dir: str | Path = "cog-ai-results/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _risk_score(self, findings: list[dict]) -> float:
        if not findings:
            return 0.0
        return round(
            sum(SEVERITY_SCORE.get(f.get("severity", "info"), 0) for f in findings) / len(findings),
            2,
        )

    def generate_all(self, target: str, findings: list[dict], chains: list | None = None) -> dict:
        ts = time.strftime("%Y%m%d_%H%M%S")
        base = self.output_dir / f"{target.replace('/', '_')}_{ts}"
        paths = {
            "json": self._write_json(base.with_suffix(".json"), target, findings, chains),
            "markdown": self._write_markdown(base.with_suffix(".md"), target, findings, chains),
            "html": self._write_html(base.with_suffix(".html"), target, findings, chains),
        }
        return paths

    def _write_json(self, path: Path, target: str, findings: list, chains: list | None) -> str:
        doc = {
            "target": target,
            "generated_at": time.time(),
            "risk_score": self._risk_score(findings),
            "findings": findings,
            "attack_chains": chains or [],
        }
        path.write_text(json.dumps(doc, indent=2))
        return str(path)

    def _write_markdown(self, path: Path, target: str, findings: list, chains: list | None) -> str:
        lines = [
            f"# Security Assessment: {target}",
            f"**Risk Score:** {self._risk_score(findings)}/10",
            "",
            "## Executive Summary",
            f"- Validated findings: {len(findings)}",
            "",
            "## Findings",
        ]
        for f in findings:
            poc = f.get("poc", {})
            curl = poc.get("curl_command", "N/A") if isinstance(poc, dict) else "N/A"
            lines.extend(
                [
                    f"### {f.get('title', f.get('vuln_type', 'Finding'))}",
                    f"- **Severity:** {f.get('severity', 'unknown')}",
                    f"- **URL:** {f.get('url', 'N/A')}",
                    f"- **PoC:** `{curl}`",
                    f"- **Remediation:** {f.get('remediation', f.get('remediation_patch', {}).get('patch_snippet', 'See patch'))}",
                    "",
                ]
            )
        if chains:
            lines.append("## Attack Chains")
            for c in chains:
                lines.append(f"- {c}")
        path.write_text("\n".join(lines))
        return str(path)

    def _write_html(self, path: Path, target: str, findings: list, chains: list | None) -> str:
        rows = "".join(
            f"<tr><td>{html.escape(str(f.get('severity', '')))}</td>"
            f"<td>{html.escape(str(f.get('title', f.get('vuln_type', ''))))}</td>"
            f"<td>{html.escape(str(f.get('url', '')))}</td></tr>"
            for f in findings
        )
        doc = f"""<!DOCTYPE html>
<html><head><title>SecAgent Report — {html.escape(target)}</title>
<style>body{{font-family:sans-serif;margin:2rem}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:8px}}th{{background:#1a1a2e;color:#fff}}</style></head>
<body><h1>SecAgent Report: {html.escape(target)}</h1>
<p>Risk Score: <strong>{self._risk_score(findings)}</strong></p>
<table><tr><th>Severity</th><th>Title</th><th>URL</th></tr>{rows}</table>
</body></html>"""
        path.write_text(doc)
        return str(path)
