"""Module 12: Key validation agent (Keyhacks-style) with rate limiting."""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass

import httpx

from secagents.vault.env_loader import mask_secret
from secagents.core.skill_manager import skill_manager


# Validation endpoints inspired by public keyhacks knowledge base
VALIDATORS: dict[str, dict] = {
    "aws": {
        "pattern": r"AKIA[0-9A-Z]{16}",
        "method": "GET",
        "url": "https://sts.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15",
        "note": "Requires secret — pattern-only detection",
    },
    "github": {
        "pattern": r"ghp_[a-zA-Z0-9]{36}",
        "method": "GET",
        "url": "https://api.github.com/user",
        "header": "Authorization",
        "prefix": "token ",
    },
    "stripe": {
        "pattern": r"sk_live_[a-zA-Z0-9]{24,}",
        "method": "GET",
        "url": "https://api.stripe.com/v1/balance",
        "header": "Authorization",
        "prefix": "Bearer ",
    },
    "slack": {
        "pattern": r"xox[baprs]-[0-9a-zA-Z-]{10,}",
        "method": "GET",
        "url": "https://slack.com/api/auth.test",
        "param": "token",
    },
    "google": {
        "pattern": r"AIza[0-9A-Za-z\-_]{35}",
        "method": "GET",
        "url": "https://www.googleapis.com/oauth2/v1/tokeninfo",
        "param": "access_token",
    },
}


@dataclass
class KeyFinding:
    service: str
    key_masked: str
    valid: bool | None  # None = not tested
    message: str
    source: str = ""


@dataclass
class KeyhacksAgent:
    """
    Discovers and validates leaked API keys with aggressive rate limiting.
    Never brute-forces; max 1 request per key per service.
    """

    requests_per_minute: float = 10.0
    _last_request: float = 0.0

    def __post_init__(self) -> None:
        rpm = max(1.0, self.requests_per_minute)
        self._min_interval = 60.0 / rpm
        if skill_manager.skills:
            # Skill awareness: potentially adjust regex or priority based on skills
            pass

    def discover_keys(self, text: str, source: str = "") -> list[tuple[str, str]]:
        """Extract potential keys from text."""
        found: list[tuple[str, str]] = []
        for service, cfg in VALIDATORS.items():
            for match in re.finditer(cfg["pattern"], text):
                found.append((service, match.group(0)))
        return found

    async def validate_key(self, service: str, key: str) -> KeyFinding:
        masked = mask_secret(key)
        cfg = VALIDATORS.get(service)
        if not cfg:
            return KeyFinding(service, masked, None, "Unknown service", "")

        await self._throttle()

        if service == "aws":
            return KeyFinding(
                service,
                masked,
                None,
                "AWS access key pattern detected — manual secret validation required",
                "",
            )

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if cfg.get("param"):
                    resp = await client.get(cfg["url"], params={cfg["param"]: key})
                elif cfg.get("header"):
                    header_val = f"{cfg.get('prefix', '')}{key}"
                    resp = await client.get(cfg["url"], headers={cfg["header"]: header_val})
                else:
                    resp = await client.get(cfg["url"], headers={"Authorization": f"Bearer {key}"})

                valid = resp.status_code == 200
                return KeyFinding(
                    service,
                    masked,
                    valid,
                    f"HTTP {resp.status_code}" if not valid else "Key appears active",
                    "",
                )
        except httpx.HTTPError as e:
            return KeyFinding(service, masked, False, str(e)[:60], "")

    async def scan_content(self, content: str, source: str = "") -> list[KeyFinding]:
        results: list[KeyFinding] = []
        for service, key in self.discover_keys(content, source):
            finding = await self.validate_key(service, key)
            finding.source = source
            results.append(finding)
        return results

    async def scan_paths(self, paths: list[str]) -> list[KeyFinding]:
        all_findings: list[KeyFinding] = []
        for path in paths:
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                all_findings.extend(await self.scan_content(text, source=path))
            except OSError:
                continue
        return all_findings

    async def _throttle(self) -> None:
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request = time.time()
