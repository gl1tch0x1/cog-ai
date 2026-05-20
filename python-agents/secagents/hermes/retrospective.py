"""Post-scan retrospective agent — commits learnings to Hermes memory."""

from __future__ import annotations

from secagents.hermes.store import HermesMemory


class RetrospectiveAgent:
    """Analyze completed scan and update long-term memory."""

    def __init__(self, memory: HermesMemory | None = None):
        self.memory = memory or HermesMemory()

    def analyze(self, scan_results: dict) -> dict:
        target = scan_results.get("target", "unknown")
        findings = scan_results.get("findings", [])
        learnings: list[str] = []

        for f in findings:
            if f.get("validated") or f.get("poc_verified"):
                self.memory.log_success(
                    target,
                    f.get("type", f.get("title", "unknown")),
                    {"url": f.get("url"), "severity": f.get("severity")},
                )
                learnings.append(f"Success: {f.get('title', 'finding')}")
            elif f.get("false_positive"):
                self.memory.log_failure(
                    target,
                    f.get("type", "unknown"),
                    "false_positive_after_validation",
                    {"title": f.get("title")},
                )

        # Generate skill stub for repeated successful patterns
        types = {f.get("type") for f in findings if f.get("validated")}
        for t in types:
            if t:
                skill_name = f"auto_{t}_{target.replace('.', '_')[:30]}"
                self.memory.save_skill(
                    skill_name,
                    f"# Auto-generated skill for {t} on {target}\n# Review before production use\n",
                    language="python",
                )

        summary = {
            "target": target,
            "findings_count": len(findings),
            "learnings_recorded": len(learnings),
            "skills_total": len(self.memory.get_skills()),
        }
        return summary
