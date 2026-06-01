"""Unified pipeline: Pre-flight → Vault → Armada → Crucible → Remediation → Hermes."""

from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console
from rich.text import Text

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
        self.console = Console()

    async def run(self) -> dict:
        # 0. Scope gate (fail-closed)
        try:
            domain = enforce_scope(self.target)
            self.results["domain"] = domain
        except ScopeViolationError as e:
            self.console.print(f"[bold red]⛔ Scope Violation:[/bold red] {e}")
            raise SystemExit(1) from e

        # 1. Pre-flight
        ok, msg = check_os_security_updates(skip=self.skip_os_check)
        if not ok:
            self.console.print(f"[bold red]CRITICAL:[/bold red] {OS_UPDATE_MESSAGE}")
            raise SystemExit(1)
        self.results["phases"]["preflight"] = {"os_check": msg}

        # 2. The Vault
        from secagents.core.skill_manager import skill_manager
        if skill_manager.skills:
             self.console.print(f"[bold green]🔥[/bold green] [white]Advanced Hunting Skills loaded from SKILL.md[/white]")
        
        vault = Vault()
        await vault.validate_all()
        # vault.print_status() # CLI handles this now
        
        if not vault.any_llm_available() and not os.environ.get("OLLAMA_HOST"):
            self.console.print("[bold yellow]⚠️  No LLM keys validated — attempting local Ollama fallback[/bold yellow]")
            setup_ollama(pull=self.setup_local_llm)

        if self.setup_local_llm:
            hw = detect_hardware()
            self.console.print(f"  [cyan]Hardware:[/cyan] {hw.summary()}")
            _, ollama_msg = setup_ollama(pull=True)
            self.console.print(f"  [cyan]whichllm:[/cyan] {ollama_msg}")

        llm = OmniLLM()
        consensus = ConsensusEngine(llm=llm, min_agreement=2 if len(llm.providers) >= 2 else 1)

        # 3. Fortress sandbox
        sandbox = None
        if self.use_sandbox:
            try:
                sandbox = FortressSandbox(self.results_dir)
                self.results["run_dir"] = str(sandbox.run_dir)
                if not sandbox.ensure_image():
                    self.console.print("[yellow]⚠️  Fortress image missing — build: docker build -t secagents/sandbox:latest -f sandbox/Dockerfile sandbox/[/yellow]")
            except RuntimeError as e:
                self.console.print(f"[yellow]⚠️  Fortress unavailable: {e}[/yellow]")

        # 4. External intel
        self.console.print("[bold blue]󰋼[/bold blue] [white]Extracting external intelligence...[/white]")
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

        # 5. The Armada — execute full DAG
        self.console.print("[bold blue]󰋼[/bold blue] [white]Deploying agent swarm (The Armada)...[/white]")
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

        # Secondary: Arsenal heuristic probes
        if self.arsenal_secondary:
            self.console.print("[bold blue]󰋼[/bold blue] [white]Engaging secondary heuristic probes (The Arsenal)...[/white]")
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

        # Deduplicate
        seen: set[str] = set()
        unique: list[dict] = []
        for f in raw_findings:
            key = f"{f.get('url', '')}|{f.get('type', f.get('vuln_type', ''))}"
            if key not in seen:
                seen.add(key)
                unique.append(f)

        # 6. The Crucible
        self.console.print("[bold blue]󰋼[/bold blue] [white]Validating signals and correlating chains (The Crucible)...[/white]")
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
        self.console.print("[bold blue]󰋼[/bold blue] [white]Generating breach reports and auto-patches...[/white]")
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
        self.console.print("[bold blue]󰋼[/bold blue] [white]Archiving mission data to persistent memory...[/white]")
        hermes = HermesMemory(self.results_dir / "hermes" / "memory.db")
        retro = RetrospectiveAgent(hermes)
        self.results["hermes"] = retro.analyze(self.results)
        hermes.export_json(self.results_dir / "hermes" / "export.json")

        return self.results
