"""Unified pipeline: Pre-flight → Vault → Armada → Crucible → Remediation → Hermes."""

from __future__ import annotations

import os
from pathlib import Path

from secagents.operational.integrity import check_os_security_updates, OS_UPDATE_MESSAGE
from secagents.vault.env_loader import Vault
from secagents.whichllm.hardware import detect_hardware, setup_ollama
from secagents.armada.swarm import ArmadaOrchestrator
from secagents.armada.handlers import build_scan_handlers
from secagents.arsenal.exploits import ArsenalScanner
from secagents.crucible.validation import CrucibleValidator
from secagents.crucible.regression import RegressionRegistry
from secagents.remediation.patcher import AutoPatcher
from secagents.remediation.reporter import ReportGenerator
from secagents.hermes.retrospective import RetrospectiveAgent
from secagents.hermes.store import HermesMemory
from secagents.intel.shodan_client import ShodanIntel
from secagents.intel.chaos_client import ChaosIntel
from secagents.fortress.sandbox import FortressSandbox
from secagents.engine.ci_notifier import CINotifier
from secagents.llm.omni import OmniLLM
from secagents.llm.consensus import ConsensusEngine
from secagents.infra.scope import enforce_scope, ScopeViolationError


class ScanPipeline:
    """Production scan pipeline with scope enforcement and deterministic checks."""

    def __init__(
        self,
        target: str,
        depth: str = "standard",
        workers: int = 4,
        use_sandbox: bool = True,
        skip_os_check: bool = False,
        setup_local_llm: bool = False,
        results_dir: Path | None = None,
        arsenal_secondary: bool = True,
    ):
        self.target = target
        self.depth = depth
        self.workers = workers
        self.use_sandbox = use_sandbox
        self.skip_os_check = skip_os_check
        self.setup_local_llm = setup_local_llm
        self.results_dir = results_dir or Path(os.environ.get("RESULTS_DIR", "cog-ai-results"))
        self.arsenal_secondary = arsenal_secondary
        self.results: dict = {"target": target, "phases": {}, "findings": [], "chains": []}

    async def run(self) -> dict:
        # 0. Scope gate (fail-closed)
        try:
            domain = enforce_scope(self.target)
            self.results["domain"] = domain
        except ScopeViolationError as e:
            raise SystemExit(f"⛔ Scope violation: {e}") from e

        # 1. Pre-flight — OS security updates only (no auto git pull on scan)
        ok, msg = check_os_security_updates(skip=self.skip_os_check)
        if not ok:
            raise SystemExit(OS_UPDATE_MESSAGE)
        self.results["phases"]["preflight"] = {"os_check": msg}

        # 2. The Vault
        from secagents.core.skill_manager import skill_manager
        if skill_manager.skills:
             print(f"🔥 Advanced Hunting Skills loaded from SKILL.md")
        
        vault = Vault()
        await vault.validate_all()
        vault.print_status()
        if not vault.any_llm_available() and not os.environ.get("OLLAMA_HOST"):
            print("⚠️  No LLM keys validated — attempting local Ollama setup")
            setup_ollama(pull=self.setup_local_llm)

        if self.setup_local_llm:
            hw = detect_hardware()
            print(f"  Hardware: {hw.summary()}")
            _, ollama_msg = setup_ollama(pull=True)
            print(f"  whichllm: {ollama_msg}")

        llm = OmniLLM()
        consensus = ConsensusEngine(llm=llm, min_agreement=2 if len(llm.providers) >= 2 else 1)

        # 3. Fortress sandbox (optional)
        sandbox = None
        if self.use_sandbox:
            try:
                sandbox = FortressSandbox(self.results_dir)
                self.results["run_dir"] = str(sandbox.run_dir)
                if not sandbox.ensure_image():
                    print("⚠️  Fortress image missing — build: docker build -t secagents/sandbox:latest -f sandbox/Dockerfile sandbox/")
            except RuntimeError as e:
                print(f"⚠️  Fortress unavailable: {e}")

        # 4. External intel
        intel: dict = {}
        chaos = ChaosIntel()
        shodan = ShodanIntel()
        if chaos.available:
            subs = await chaos.subdomains(domain)
            intel["chaos_subdomains"] = subs[:500]
            self.results["phases"]["chaos"] = {"count": len(subs)}
        if shodan.available:
            dns_data = await shodan.search_domain(domain)
            intel["shodan"] = dns_data
            self.results["phases"]["shodan"] = {"records": len(dns_data)}

        # 5. The Armada — execute full DAG with real handlers
        shared: dict = {
            "target": domain,
            "depth": self.depth,
            "intel": intel,
            "raw_findings": [],
            "endpoints": [],
        }
        armada = ArmadaOrchestrator(workers=self.workers)
        for name, handler in build_scan_handlers(shared).items():
            armada.register_handler(name, handler)

        graph = armada.plan_mission(domain, self.depth)
        armada_results = await armada.execute(graph, shared)
        raw_findings = list(armada_results.get("findings", [])) or shared.get("raw_findings", [])

        self.results["phases"]["armada"] = {
            "tasks": len(graph.tasks),
            "task_results": len(armada_results.get("tasks", {})),
            "specialists": [s.name for s in armada.hire_specialists(graph)],
        }

        # Secondary: Arsenal heuristic probes (require Crucible proof)
        if self.arsenal_secondary:
            scanner = ArsenalScanner(verify_ssl=True)
            endpoints = shared.get("endpoints") or [f"https://{domain}"]
            limit = 25 if self.depth == "quick" else 50 if self.depth == "standard" else 100
            for url in endpoints[:limit]:
                for p in await scanner.scan_url(url):
                    raw_findings.append({
                        "title": f"{p.vuln_type.upper()} in {p.parameter}",
                        "type": p.vuln_type,
                        "vuln_type": p.vuln_type,
                        "url": p.url,
                        "parameter": p.parameter,
                        "payload": p.payload,
                        "evidence": p.evidence,
                        "proof_signal": p.evidence,
                        "severity": "medium",
                        "confidence": p.confidence,
                        "source": "arsenal",
                        "deterministic": False,
                    })

        # Deduplicate by url + type
        seen: set[str] = set()
        unique: list[dict] = []
        for f in raw_findings:
            key = f"{f.get('url', '')}|{f.get('type', f.get('vuln_type', ''))}"
            if key not in seen:
                seen.add(key)
                unique.append(f)

        # 6. The Crucible
        crucible = CrucibleValidator(consensus=consensus)
        validated = await crucible.validate_batch(unique)
        self.results["findings"] = validated
        self.results["chains"] = await crucible.correlate_chains(validated)
        await crucible.aclose()
        await llm.aclose()

        registry = RegressionRegistry(self.results_dir / "regression")
        for f in validated:
            registry.register(f)

        # 7. Remediation
        patcher = AutoPatcher()
        patcher.apply_to_findings(validated)
        reporter = ReportGenerator(self.results_dir / "reports")
        report_paths = reporter.generate_all(domain, validated, self.results["chains"])
        self.results["reports"] = report_paths

        if sandbox:
            sandbox.write_log("scan_summary.log", f"findings={len(validated)}\n")

        notifier = CINotifier()
        if report_paths.get("markdown"):
            await notifier.notify_slack(validated, report_paths["markdown"])
            await notifier.create_jira_tickets(validated)

        # 8. Hermes
        hermes = HermesMemory(self.results_dir / "hermes" / "memory.db")
        retro = RetrospectiveAgent(hermes)
        self.results["hermes"] = retro.analyze(self.results)
        hermes.export_json(self.results_dir / "hermes" / "export.json")

        return self.results
