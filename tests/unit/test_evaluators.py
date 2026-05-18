"""Unit tests for evaluators."""

from secagents.evaluators import evaluate_confidence, evaluate_completeness, evaluate_finding


def test_confidence_passes():
    result = evaluate_confidence({"confidence": 0.85}, min_confidence=0.7)
    assert result.passed is True
    assert result.score == 0.85


def test_confidence_fails():
    result = evaluate_confidence({"confidence": 0.4}, min_confidence=0.7)
    assert result.passed is False


def test_completeness_all_present():
    output = {"result": {"findings": [], "endpoints_tested": 5}}
    result = evaluate_completeness(output, ["findings", "endpoints_tested"])
    assert result.passed is True


def test_completeness_missing_fields():
    output = {"result": {"findings": []}}
    result = evaluate_completeness(output, ["findings", "endpoints_tested"])
    assert result.passed is False
    assert result.score == 0.5


def test_finding_evaluation():
    finding = {
        "title": "XSS",
        "severity": "high",
        "summary": "Reflected XSS in search",
        "steps": "1. Go to /search?q=<script>",
        "impact": "Session hijacking",
        "remediation": "Encode output",
    }
    result = evaluate_finding(finding)
    assert result.passed is True
    assert result.score == 1.0


def test_incomplete_finding():
    finding = {"title": "Something", "severity": "low"}
    result = evaluate_finding(finding)
    assert result.passed is False
