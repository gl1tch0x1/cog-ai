"""Portable Proof Capsule serialization and single-vulnerability replay engine."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("secagents.proof_capsule")


@dataclass
class ProofCapsule:
    id: str
    target_url: str
    vuln_type: str
    title: str
    severity: str
    http_method: str
    request_headers: Dict[str, str]
    request_body: Optional[str]
    query_params: Dict[str, str]
    proof_signal: str
    timestamp: float
    metadata: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> ProofCapsule:
        data = json.loads(json_str)
        return cls(**data)

    def save(self, filepath: Path) -> Path:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(self.to_json(), encoding="utf-8")
        logger.info(f"Saved proof capsule {self.id} to {filepath}")
        return filepath


class ProofCapsuleReplayer:
    """Zero-dependency replay engine for SecAgent proof capsules."""

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout = timeout_seconds

    async def replay_async(self, capsule: ProofCapsule) -> tuple[bool, str]:
        """Replay proof capsule HTTP request and check if target remains vulnerable."""
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, verify=False) as client:
            try:
                method = capsule.http_method.upper()
                headers = capsule.request_headers or {}
                params = capsule.query_params or {}

                if method == "POST":
                    resp = await client.post(capsule.target_url, headers=headers, params=params, data=capsule.request_body)
                elif method == "PUT":
                    resp = await client.put(capsule.target_url, headers=headers, params=params, data=capsule.request_body)
                else:
                    resp = await client.get(capsule.target_url, headers=headers, params=params)

                is_vulnerable = capsule.proof_signal in resp.text
                status_msg = (
                    f"[VERIFIED] Target remains vulnerable! Proof signal '{capsule.proof_signal}' detected (HTTP {resp.status_code})"
                    if is_vulnerable
                    else f"[PATCHED / CLEAN] Proof signal '{capsule.proof_signal}' not present in response (HTTP {resp.status_code})"
                )
                return is_vulnerable, status_msg
            except Exception as e:
                return False, f"[REPLAY ERROR] Failed to connect to target: {e}"

    def replay_file(self, capsule_path: Path) -> tuple[bool, str]:
        """Synchronous helper to read capsule file and replay."""
        import asyncio
        capsule = ProofCapsule.from_json(capsule_path.read_text(encoding="utf-8"))
        return asyncio.run(self.replay_async(capsule))
