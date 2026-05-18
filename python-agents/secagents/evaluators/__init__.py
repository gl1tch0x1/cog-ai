"""Evaluators for agent output quality."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvalResult:
    score: float  # 0.0 - 1.0
    passed: bool
    feedback: str


def evaluate_confidence(output: dict, min_confidence: float = 0.7) -> EvalResult:
    """Check if agent output meets minimum confidence threshold."""
    conf = output.get("confidence", 0.0)
    passed = conf >= min_confidence
    return EvalResult(
        score=conf,
        passed=passed,
        feedback=f"Confidence {conf:.2f} {'meets' if passed else 'below'} threshold {min_confidence}",
    )


def evaluate_completeness(output: dict, required_fields: list[str]) -> EvalResult:
    """Check if output contains all required fields."""
    result = output.get("result", {})
    missing = [f for f in required_fields if f not in result]
    score = 1.0 - (len(missing) / max(len(required_fields), 1))
    return EvalResult(
        score=score,
        passed=len(missing) == 0,
        feedback=f"Missing fields: {missing}" if missing else "All fields present",
    )


def evaluate_finding(finding: dict) -> EvalResult:
    """Evaluate a security finding for report-readiness."""
    required = ["title", "severity", "summary", "steps", "impact", "remediation"]
    present = sum(1 for f in required if finding.get(f))
    score = present / len(required)
    missing = [f for f in required if not finding.get(f)]
    return EvalResult(
        score=score,
        passed=score >= 0.8,
        feedback=f"Finding completeness: {score:.0%}. Missing: {missing}" if missing else "Complete",
    )
