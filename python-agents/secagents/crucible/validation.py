"""Module 7: PoC validation, exploit chaining, strict false-positive control."""

from __future__ import annotations

import os
import re

import httpx

from secagents.engine.poc_generator import PoCGenerator
from secagents.llm.consensus import ConsensusEngine
from secagents.modules.exploit_chain import correlate_chains


class CrucibleValidator:
    """
    Validates findings with deterministic proof and/or LLM consensus.
    Non-deterministic (Arsenal) findings require proof_signal + pattern match.
    """

    def __init__(self, consensus: ConsensusEngine | None = None, verify_ssl: bool | None = None):
        self.poc_gen = PoCGenerator()
        self.consensus = consensus or ConsensusEngine()
        if verify_ssl is None:
            verify_ssl = os.environ.get("SECAGENT_VERIFY_SSL", "true").lower() != "false"
        self.verify_ssl = verify_ssl
        self._client = httpx.AsyncClient(timeout=20, verify=self.verify_ssl, follow_redirects=True)

    async def validate_finding(self, finding: dict) -> dict:
        poc = self.poc_gen.generate(finding)
        finding["poc"] = poc

        # Deterministic CVE findings: proof_signal required
        if finding.get("deterministic") or finding.get("source") == "cve_checks":
            poc_verified = bool(finding.get("proof_signal")) and await self._replay_deterministic(finding)
        else:
            poc_verified = await self._execute_poc_strict(finding, poc)

        finding["poc_verified"] = poc_verified
        if not poc_verified:
            finding["validated"] = False
            finding["false_positive"] = True
            return finding

        consensus = await self.consensus.verify_finding(finding)
        finding["consensus"] = {
            "agreed": consensus.agreed,
            "votes": consensus.votes,
            "summary": consensus.summary,
        }
        finding["validated"] = consensus.agreed
        finding["false_positive"] = not consensus.agreed
        return finding

    async def validate_batch(self, findings: list[dict]) -> list[dict]:
        validated = []
        for f in findings:
            result = await self.validate_finding(f)
            if result.get("validated"):
                validated.append(result)
        return validated

    async def correlate_chains(self, findings: list[dict]) -> list[dict]:
        return correlate_chains(findings)

    async def _replay_deterministic(self, finding: dict) -> bool:
        url = finding.get("poc_url") or finding.get("url", finding.get("location", ""))
        proof = finding.get("proof_signal", "")
        if not url or not proof:
            return False
        try:
            resp = await self._client.get(url)
            return proof.lower() in resp.text.lower()
        except httpx.HTTPError:
            return False

    async def _execute_poc_strict(self, finding: dict, poc: dict) -> bool:
        url = finding.get("url", finding.get("location", ""))
        if not url:
            return False

        proof = finding.get("proof_signal") or finding.get("evidence", "")
        if not proof:
            return False

        try:
            resp = await self._client.get(url)
            body = resp.text[:100_000]
            payload = finding.get("payload", "")

            if payload and len(payload) >= 4 and payload in body:
                return True

            # Evidence must be a regex pattern or substantive string (not generic "error")
            if proof.lower() in ("matched pattern", "error", "warning"):
                return False

            if proof.startswith("Matched pattern:"):
                pat = proof.split(":", 1)[-1].strip()
                try:
                    return bool(re.search(pat, body, re.I))
                except re.error:
                    return False

            return proof.lower() in body.lower()
        except httpx.HTTPError:
            return False

    async def aclose(self) -> None:
        await self._client.aclose()
