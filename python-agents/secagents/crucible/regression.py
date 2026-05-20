"""Auto-generated regression tests for discovered vulnerability patterns."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class RegressionRegistry:
    """Store and run regression tests so patterns are never missed."""

    def __init__(self, registry_dir: str | Path = "cog-ai-results/regression"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

    def _fingerprint(self, finding: dict) -> str:
        raw = f"{finding.get('vuln_type', '')}|{finding.get('type', '')}|{finding.get('parameter', '')}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def register(self, finding: dict) -> Path:
        """Generate regression test file for a validated finding."""
        fp = self._fingerprint(finding)
        path = self.registry_dir / f"test_{fp}.json"
        spec = {
            "vuln_type": finding.get("vuln_type", finding.get("type")),
            "url_pattern": finding.get("url", ""),
            "parameter": finding.get("parameter", ""),
            "payload": finding.get("payload", ""),
            "evidence": finding.get("evidence", ""),
        }
        path.write_text(json.dumps(spec, indent=2))
        return path

    def list_tests(self) -> list[dict]:
        tests = []
        for p in self.registry_dir.glob("test_*.json"):
            try:
                tests.append(json.loads(p.read_text()))
            except json.JSONDecodeError:
                continue
        return tests

    def match_finding(self, candidate: dict) -> bool:
        """Check if candidate matches any registered regression pattern."""
        for spec in self.list_tests():
            if spec.get("vuln_type") == candidate.get("vuln_type", candidate.get("type")):
                if spec.get("parameter") == candidate.get("parameter"):
                    return True
        return False
