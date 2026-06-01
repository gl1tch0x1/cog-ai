"""Default Armada task handlers wired to real agents and scanners."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from secagents.agents.validator import ValidatorAgent
from secagents.modules.autopilot import Autopilot
from secagents.modules.cve_scanner import CVEScanner, ScanConfig


def cve_result_to_finding(result) -> dict:
    sev = result.severity.value if hasattr(result.severity, "value") else str(result.severity)
    return {
        "title": result.name,
        "type": result.name,
        "vuln_type": result.name,
        "url": result.target_url,
        "location": result.target_url,
        "poc_url": result.poc_url,
        "payload": "",
        "evidence": result.proof_signal,
        "proof_signal": result.proof_signal,
        "severity": sev,
        "confidence": 0.95,
        "source": "cve_checks",
        "deterministic": True,
    }


def build_scan_handlers(
    shared: dict[str, Any],
) -> dict[str, Callable[..., Awaitable[dict]]]:
    """
    Build handlers that mutate `shared` context:
      target, depth, intel, endpoints, raw_findings, ...
    """

    async def recon_handler(*, context: dict, action: str, **_) -> dict:
        target = context.get("target", shared["target"])
        autopilot = Autopilot(
            target, {"depth": shared.get("depth", "standard"), "intel": shared.get("intel", {})}
        )
        await autopilot._phase_recon()
        endpoints = autopilot.results.get("endpoints", [])
        if not endpoints:
            endpoints = [f"https://{target}", f"http://{target}"]
        shared["endpoints"] = endpoints
        shared["autopilot"] = autopilot
        return {"endpoints": len(endpoints), "findings": []}

    async def scan_handler(*, context: dict, action: str, **_) -> dict:
        target = shared["target"]
        depth = shared.get("depth", "standard")
        threads = 20 if depth == "deep" else 10 if depth == "standard" else 5

        findings: list[dict] = []

        # Deterministic CVE engine (primary)
        scanner = CVEScanner(
            ScanConfig(target=target, threads=threads, timeout=12, verify_ssl=True)
        )
        progress = await scanner.run()
        for r in progress.findings:
            if r.vulnerable:
                findings.append(cve_result_to_finding(r))

        # Autopilot external tools (nuclei, etc.) when available
        autopilot = shared.get("autopilot")
        if autopilot is None:
            autopilot = Autopilot(target, {"depth": depth})
            await autopilot._phase_recon()
        await autopilot._phase_scan()
        for f in autopilot.results.get("findings", []):
            if isinstance(f, dict) and f.get("severity", "info") != "info":
                f.setdefault("source", "autopilot")
                findings.append(f)

        shared["raw_findings"] = findings
        return {"findings": findings, "cve_count": len(progress.findings)}

    async def validate_handler(*, context: dict, action: str, **_) -> dict:
        agent = ValidatorAgent()
        raw = shared.get("raw_findings", [])
        output = await agent.execute({"findings": raw, "action": "validate_batch"})
        validated = output.result.get("validated", raw) if isinstance(output.result, dict) else raw
        shared["agent_validated"] = validated
        return {"findings": validated}

    async def report_handler(*, context: dict, action: str, **_) -> dict:
        return {"status": "report_deferred", "findings": shared.get("agent_validated", [])}

    return {
        "subdomain": recon_handler,
        "web_crawl": recon_handler,
        "port_scan": recon_handler,
        "sqli": scan_handler,
        "xss": scan_handler,
        "ssrf": scan_handler,
        "idor": scan_handler,
        "validator": validate_handler,
    }
