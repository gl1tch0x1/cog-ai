"""Multi-provider consensus for critical findings (2-of-N agreement)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from secagents.llm.omni import LLMMessage, OmniLLM


@dataclass
class ConsensusResult:
    agreed: bool
    votes: list[dict]
    agreement_count: int
    min_required: int
    summary: str


class ConsensusEngine:
    """Require 2-of-3 (or configurable) LLM agreement before reporting."""

    def __init__(self, llm: OmniLLM | None = None, min_agreement: int = 2):
        self.llm = llm or OmniLLM()
        self.min_agreement = min_agreement

    async def verify_finding(self, finding: dict) -> ConsensusResult:
        providers = self.llm.providers[:3]
        if len(providers) < 2:
            # Single provider: require structured JSON affirm
            single = await self._ask_provider(providers[0].name if providers else None, finding)
            agreed = single.get("valid", False) and single.get("confidence", 0) >= 0.75
            return ConsensusResult(
                agreed=agreed,
                votes=[single],
                agreement_count=1 if agreed else 0,
                min_required=1,
                summary="Single-provider mode (add more LLM_API_KEYS for 2-of-N consensus)",
            )

        votes: list[dict] = []
        for cfg in providers:
            try:
                vote = await self._ask_provider(cfg.name, finding)
                votes.append(vote)
            except Exception as e:
                votes.append({"provider": cfg.name, "valid": False, "error": str(e)[:80]})

        positive = sum(
            1 for v in votes
            if v.get("valid") and float(v.get("confidence", 0)) >= 0.75
        )
        agreed = positive >= self.min_agreement
        return ConsensusResult(
            agreed=agreed,
            votes=votes,
            agreement_count=positive,
            min_required=self.min_agreement,
            summary=f"{positive}/{len(votes)} providers agree" if agreed else "Consensus not reached",
        )

    async def _ask_provider(self, provider: str | None, finding: dict) -> dict:
        prompt = (
            "You are a security validator. Analyze this finding and respond ONLY with JSON:\n"
            '{"valid": true|false, "confidence": 0.0-1.0, "severity": "...", "reason": "..."}\n\n'
            f"Finding:\n{json.dumps(finding, indent=2)[:4000]}"
        )
        resp = await self.llm.complete(
            [LLMMessage("user", prompt)],
            provider=provider,
            max_tokens=256,
        )
        return self._parse_vote(resp.provider, resp.content)

    @staticmethod
    def _parse_vote(provider: str, text: str) -> dict:
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return {
                    "provider": provider,
                    "valid": bool(data.get("valid")),
                    "confidence": float(data.get("confidence", 0.5)),
                    "reason": data.get("reason", ""),
                }
            except (json.JSONDecodeError, ValueError):
                pass
        valid = "true" in text.lower() and "invalid" not in text.lower()
        return {"provider": provider, "valid": valid, "confidence": 0.5, "reason": text[:200]}
