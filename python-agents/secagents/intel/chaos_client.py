"""Module 10: Project Discovery Chaos API for subdomain enumeration."""

from __future__ import annotations

import os

import httpx


class ChaosIntel:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("CHAOS_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def subdomains(self, domain: str) -> list[str]:
        if not self.available:
            return []
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://dns.projectdiscovery.io/dns/{domain}/subdomains",
                headers={"Authorization": self.api_key},
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                return data.get("subdomains", data.get("results", []))
        return []
