"""Tests for Crucible regression registry."""

import tempfile
from pathlib import Path

from secagents.crucible.regression import RegressionRegistry


def test_register_and_match():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegressionRegistry(tmp)
        finding = {"vuln_type": "sqli", "parameter": "id", "url": "http://test"}
        path = reg.register(finding)
        assert path.exists()
        assert reg.match_finding({"vuln_type": "sqli", "parameter": "id"})
        assert not reg.match_finding({"vuln_type": "xss", "parameter": "id"})
