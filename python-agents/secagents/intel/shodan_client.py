"""Module 10: Shodan integration for recon phase."""

from __future__ import annotations

import os

import httpx


class ShodanIntel:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("SHODAN_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def host_info(self, ip: str) -> dict:
        if not self.available:
            return {}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f"https://api.shodan.io/shodan/host/{ip}",
                params={"key": self.api_key},
            )
            if resp.status_code == 200:
                return resp.json()
        return {}

    async def search_domain(self, domain: str) -> list[dict]:
        if not self.available:
            return []
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                "https://api.shodan.io/dns/domain/" + domain,
                params={"key": self.api_key},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
        return []

    async def cves_for_host(self, ip: str) -> list[str]:
        info = await self.host_info(ip)
        vulns = info.get("vulns", [])
        return list(vulns) if isinstance(vulns, list) else []
