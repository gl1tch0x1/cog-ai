"""CVE exploitation scanner: multi-phase pipeline with deterministic checks."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import httpx

from secagents.modules.cve_checks import (
    CheckDefinition,
    CheckResult,
    build_payloads,
    get_checks_for_url,
    verify_finding,
)
from secagents.modules.external_tools import ExternalTools
from secagents.infra.logging_system import AuditLogger, AuditCategory


@dataclass
class ScanConfig:
    target: str
    threads: int = 10
    timeout: int = 10
    checks: list[str] | None = None  # None = all checks


@dataclass
class ScanProgress:
    total_urls: int = 0
    processed: int = 0
    findings: list[CheckResult] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def severity_counts(self) -> dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in self.findings:
            counts[f.severity.value] += 1
        return counts


class CVEScanner:
    """5-phase exploitation pipeline inspired by TerminatorZ."""

    def __init__(self, config: ScanConfig):
        self.config = config
        self.progress = ScanProgress()
        self._logger = AuditLogger.get_instance()
        self._sem = asyncio.Semaphore(config.threads)

    async def run(self) -> ScanProgress:
        """Execute full 5-phase pipeline: Recon → Validate → Gate → Attack → Report."""
        self._logger.audit(AuditCategory.SCAN_START, f"CVE scan: {self.config.target}")

        # Phase 1: Reconnaissance
        urls = await self._phase_recon()

        # Phase 2: Validation (alive check)
        alive_urls = await self._phase_validate(urls)
        self.progress.total_urls = len(alive_urls)

        if not alive_urls:
            return self.progress

        # Phase 3: Confirmation gate (in API mode, auto-proceed)
        # Phase 4: Attack
        await self._phase_attack(alive_urls)

        # Phase 5: Results ready for reporting
        self._logger.audit(
            AuditCategory.SCAN_COMPLETE,
            f"CVE scan complete: {len(self.progress.findings)} findings from {self.progress.processed} URLs",
        )
        return self.progress

    async def _phase_recon(self) -> list[str]:
        """Multi-source recon: subfinder + waybackurls."""
        urls = set()

        # Subdomain discovery
        result = await ExternalTools.run("subfinder", self.config.target, timeout=60)
        if result.success:
            for sub in result.output:
                urls.add(f"https://{sub}/")
                urls.add(f"http://{sub}/")

        # Wayback URLs
        result = await ExternalTools.run("waybackurls", self.config.target, timeout=60)
        if result.success:
            for u in result.output:
                if u.startswith("http"):
                    urls.add(u)

        # Sanitize: drop malformed, too-long, non-http
        sanitized = []
        for u in urls:
            if len(u) <= 2000 and u.startswith("http") and " " not in u:
                sanitized.append(u)

        return sanitized

    async def _phase_validate(self, urls: list[str]) -> list[str]:
        """Validate which URLs are alive using httpx or curl fallback."""
        result = await ExternalTools.run("httpx", self.config.target, timeout=90)
        if result.success and result.output:
            return result.output

        # Fallback: parallel curl probe
        alive = []
        async with httpx.AsyncClient(verify=self.config.verify_ssl, timeout=self.config.timeout, follow_redirects=True) as client:
            sem = asyncio.Semaphore(self.config.threads * 2)

            async def probe(url: str):
                async with sem:
                    try:
                        resp = await client.head(url)
                        if resp.status_code < 500:
                            alive.append(url)
                    except Exception:
                        pass

            await asyncio.gather(*[probe(u) for u in urls[:500]])
        return alive

    async def _phase_attack(self, urls: list[str]) -> None:
        """Run checks against all alive URLs with worker pool."""
        tasks = [self._scan_url(url) for url in urls]
        await asyncio.gather(*tasks)

    async def _scan_url(self, url: str) -> None:
        """Run appropriate checks against a single URL."""
        async with self._sem:
            checks = get_checks_for_url(url)

            # Filter to selected checks if custom scan
            if self.config.checks:
                checks = [c for c in checks if c.key in self.config.checks]

            async with httpx.AsyncClient(verify=self.config.verify_ssl, timeout=self.config.timeout, follow_redirects=True) as client:
                for check in checks:
                    result = await self._run_check(client, url, check)
                    if result and result.vulnerable:
                        self.progress.findings.append(result)

            self.progress.processed += 1

    async def _run_check(self, client: httpx.AsyncClient, url: str, check: CheckDefinition) -> CheckResult | None:
        """Execute a single deterministic check."""
        payloads = build_payloads(check.key, url)

        if not payloads:
            # Header-only checks: just fetch the URL
            try:
                resp = await client.get(url)
                headers = {k.lower(): v for k, v in resp.headers.items()}
                vulnerable, proof = verify_finding(check.key, resp.text, headers, {})
                if vulnerable:
                    return CheckResult(
                        name=check.name, severity=check.severity, vulnerable=True,
                        target_url=url, poc_url=url, proof_signal=proof,
                    )
            except Exception:
                pass
            return None

        # Payload-based checks
        for payload in payloads:
            try:
                poc_url = url
                if payload.get("method") == "HEADER":
                    headers = {payload["header"]: payload["value"]}
                    resp = await client.get(url, headers=headers)
                elif payload.get("method") == "POST":
                    data = {payload["param"]: payload["value"]}
                    resp = await client.post(url, data=data)
                else:
                    sep = "&" if "?" in url else "?"
                    poc_url = f"{url}{sep}{payload['param']}={payload['value']}"
                    resp = await client.get(poc_url)

                resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                vulnerable, proof = verify_finding(check.key, resp.text, resp_headers, payload)

                if vulnerable:
                    return CheckResult(
                        name=check.name, severity=check.severity, vulnerable=True,
                        target_url=url, poc_url=poc_url, proof_signal=proof,
                    )
            except Exception:
                continue

        return None
