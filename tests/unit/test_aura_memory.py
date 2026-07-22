"""Unit test suite for AuraMemoryManager."""

import tempfile
from pathlib import Path
import pytest

from secagents.core.aura_memory import AuraMemoryManager, TargetDNA, CognitivePattern


@pytest.fixture
def temp_memory():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = Path(tmpdir) / "test_cognitive_memory.db"
        AuraMemoryManager._instance = None
        manager = AuraMemoryManager(db_path=db_path)
        yield manager
        AuraMemoryManager._instance = None


def test_remember_and_recall_target_dna(temp_memory: AuraMemoryManager):
    dna = TargetDNA(
        target="example.com",
        domain="example.com",
        tech_stack=["Nginx", "React"],
        waf_signature="Cloudflare",
        rate_limit_detected=True,
        recommended_concurrency=4,
    )

    temp_memory.remember_target_dna(dna)
    recalled = temp_memory.recall_target_dna("example.com")

    assert recalled is not None
    assert recalled.target == "example.com"
    assert recalled.waf_signature == "Cloudflare"
    assert recalled.rate_limit_detected is True
    assert "React" in recalled.tech_stack


def test_crystallize_and_recall_pattern(temp_memory: AuraMemoryManager):
    pid = temp_memory.crystallize_pattern(
        target="example.com",
        vuln_type="sqli",
        payload="' OR 1=1--",
        waf_bypassed=True,
        confidence=0.9,
    )

    assert pid.startswith("sqli:")
    patterns = temp_memory.recall_patterns_for_target("example.com")

    assert len(patterns) == 1
    assert patterns[0].vuln_type == "sqli"
    assert patterns[0].waf_bypassed is True


def test_pattern_reinforcement(temp_memory: AuraMemoryManager):
    temp_memory.crystallize_pattern("example.com", "xss", "<script>alert(1)</script>", confidence=0.8)
    temp_memory.crystallize_pattern("example.com", "xss", "<script>alert(1)</script>", confidence=0.8)

    patterns = temp_memory.recall_patterns_for_target("example.com", vuln_type="xss")
    assert len(patterns) == 1
    assert patterns[0].occurrences == 2
    assert patterns[0].confidence > 0.8


def test_memory_inspection(temp_memory: AuraMemoryManager):
    temp_memory.remember_target_dna(TargetDNA("test.com", "test.com"))
    temp_memory.crystallize_pattern("test.com", "idor", "/api/user/1")

    info = temp_memory.inspect_memory()
    assert info["target_dna_count"] >= 1
    assert info["cognitive_patterns_count"] >= 1
