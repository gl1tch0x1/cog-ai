"""Web3 security agent for smart contract and token auditing."""

import logging
import re
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import List

from secagents.agents.base import BaseAgent, AgentConfig, AgentOutput, AgentRole
from secagents.prompts import WEB3_SECURITY_PROMPT

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Finding:
    """A single red flag detected in a contract."""

    risk: RiskLevel
    category: str
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str


class Web3SecurityAgent(BaseAgent):
    """Audits smart contracts for rug-pull vectors and vulnerabilities.

    Ported from Claude Bug Bounty toolkit's token_scanner logic.
    """

    EVM_PATTERNS = {
        "hidden_mint": [
            (
                r"function\s+mint\s*\(",
                "Public mint function",
                "Contract has a mint function — check if it has a supply cap",
                RiskLevel.HIGH,
                "Verify MAX_SUPPLY is enforced in every mint path. If no cap exists, this is a CRITICAL rug vector.",
            ),
            (
                r"_mint\s*\([^)]*\)\s*;",
                "Internal _mint call",
                "Direct _mint() call found — verify it is bounded by a supply cap",
                RiskLevel.MEDIUM,
                "Trace all callers of _mint(). Each must enforce totalSupply + amount <= MAX_SUPPLY.",
            ),
            (
                r"_balances\s*\[.*\]\s*\+=",
                "Direct balance manipulation",
                "Balance increased directly without going through _mint — can inflate supply silently",
                RiskLevel.CRITICAL,
                "Balance changes MUST go through _mint/_burn. Direct manipulation bypasses supply tracking.",
            ),
            (
                r"_totalSupply\s*\+=",
                "Direct totalSupply manipulation",
                "Total supply modified directly — bypasses ERC20 mint/burn flow",
                RiskLevel.CRITICAL,
                "Total supply changes MUST go through _mint/_burn, not direct assignment.",
            ),
            (
                r"delegatecall\s*\(",
                "Delegatecall present",
                "delegatecall can execute arbitrary code including mint in the contract's context",
                RiskLevel.HIGH,
                "Verify delegatecall target is immutable and trusted. Owner-controlled delegatecall target = critical.",
            ),
        ],
        "honeypot": [
            (
                r"(?:_isBlacklisted|isBlacklisted|_blacklist|isBot|_bots|_blocked)\s*\[",
                "Blacklist mapping",
                "Contract has a blacklist that can block addresses from transferring",
                RiskLevel.CRITICAL,
                "Blacklists can be used to block all sells. Verify: can owner blacklist the DEX pair?",
            ),
            (
                r"function\s+(?:blacklist|addBot|blockAddress|setBot)\s*\(",
                "Blacklist setter function",
                "Owner can add addresses to blacklist — honeypot vector",
                RiskLevel.CRITICAL,
                "If owner can blacklist any address, they can block sells on all DEXs.",
            ),
            (
                r"maxTxAmount\s*=|_maxTxAmount|maxTransactionAmount|_maxWalletSize|maxWallet",
                "Max transaction/wallet limit",
                "Transaction or wallet size limit exists — check if setter has minimum bound",
                RiskLevel.MEDIUM,
                "Verify setMaxTx() has require(amount >= totalSupply / 1000) or similar floor.",
            ),
            (
                r"function\s+(?:setMaxTx|setMaxWallet|updateMaxTx|updateMaxWallet)\s*\(",
                "Max tx/wallet setter",
                "Owner can change max transaction limit — can be set to 0 to block all transfers",
                RiskLevel.HIGH,
                "Must have minimum bound. setMaxTx(0) = honeypot.",
            ),
            (
                r"function\s+approve.*override",
                "Approve function override",
                "approve() is overridden — can silently prevent DEX router approvals",
                RiskLevel.HIGH,
                "Verify override calls super.approve() or _approve(). Silent return = honeypot.",
            ),
            (
                r"tradingEnabled|tradingActive|canTrade|_tradingOpen",
                "Trading toggle flag",
                "Contract has a trading enabled flag — verify it cannot be toggled after enable",
                RiskLevel.MEDIUM,
                "Check: can enableTrading() be called again to disable? Should be one-way.",
            ),
            (
                r"cooldown\s*\[|_lastSell\s*\[|_lastTx\s*\[|tradeCooldown",
                "Transfer cooldown",
                "Cooldown mechanism can block sells if set to extreme values",
                RiskLevel.MEDIUM,
                "Verify cooldown is bounded (e.g., max 1 hour) and cannot be set by owner to max uint.",
            ),
        ],
        "fee_manipulation": [
            (
                r"(?:_taxFee|_sellFee|_buyFee|_liquidityFee|_marketingFee|_devFee)\s*=",
                "Tax/fee variable",
                "Contract has configurable fee — check if setter is bounded",
                RiskLevel.MEDIUM,
                "Fee setters MUST have require(fee <= MAX_FEE) with MAX_FEE <= 10%.",
            ),
            (
                r"function\s+(?:setFee|updateFee|setTax|updateTax|setBuyFee|setSellFee|setFees)\s*\(",
                "Fee setter function",
                "Owner can change buy/sell fees — can be set to 99% (rug)",
                RiskLevel.HIGH,
                "Check function body for require(fee <= MAX). Unbounded = CRITICAL.",
            ),
            (
                r"_isExcludedFromFee\s*\[|isExcludedFromFee|excludeFromFee",
                "Fee exclusion mapping",
                "Some addresses excluded from fees — owner can sell tax-free",
                RiskLevel.MEDIUM,
                "Fee exclusion for owner + 99% sell tax = classic rug pattern.",
            ),
        ],
        "lp_drain": [
            (
                r"function\s+(?:migrate|migrateLP|migrateLiquidity)\s*\(",
                "LP migration function",
                "Contract can migrate liquidity to new pair — drains old pair",
                RiskLevel.CRITICAL,
                "Migration functions allow owner to move liquidity to a controlled pair = rug.",
            ),
            (
                r"(?:emergencyWithdraw|forceWithdraw|rescueTokens|recoverTokens|rescueETH)\s*\(",
                "Emergency withdraw function",
                "Contract has emergency withdrawal — can drain locked LP or contract balance",
                RiskLevel.HIGH,
                "Verify emergency withdraw cannot access LP tokens or paired asset.",
            ),
            (
                r"(?:setPair|setNewPair|updatePair|changePair)\s*\(",
                "Pair change function",
                "DEX pair can be changed — breaks old pair trading",
                RiskLevel.CRITICAL,
                "Pair changes break all existing liquidity. Should be immutable after launch.",
            ),
        ],
        "fake_renounce": [
            (
                r"function\s+renounceOwnership.*override",
                "renounceOwnership override",
                "renounceOwnership is overridden — may not actually renounce",
                RiskLevel.CRITICAL,
                "Verify override calls _transferOwnership(address(0)). Missing = fake renounce.",
            ),
            (
                r"_shadowAdmin|_secondOwner|_backupOwner|_hiddenOwner",
                "Shadow admin pattern",
                "Secondary admin address that survives ownership renounce",
                RiskLevel.CRITICAL,
                "Second admin = fake renounce. Owner looks renounced but shadow admin retains control.",
            ),
        ],
    }

    SOLANA_PATTERNS = {
        "authority_retention": [
            (
                r"mint_authority",
                "Mint authority reference",
                "Token references mint_authority — verify it is set to None after initial mint",
                RiskLevel.HIGH,
                "Mint authority MUST be None for meme coins. Retained = infinite mint rug vector.",
            ),
            (
                r"freeze_authority",
                "Freeze authority reference",
                "Token references freeze_authority — can freeze any holder's account",
                RiskLevel.HIGH,
                "Freeze authority MUST be None for meme coins. Retained = honeypot vector.",
            ),
            (
                r"close_authority|CloseAuthority",
                "Close authority reference",
                "Token-2022 close authority — can destroy token accounts",
                RiskLevel.HIGH,
                "Close authority can destroy holder accounts. Should be None.",
            ),
        ],
        "token_2022_extensions": [
            (
                r"transfer_hook|TransferHook|spl_transfer_hook",
                "Transfer hook extension",
                "Token-2022 transfer hook — can block transfers (honeypot)",
                RiskLevel.CRITICAL,
                "Transfer hooks execute on every transfer. If owner controls hook logic = honeypot.",
            ),
            (
                r"permanent_delegate|PermanentDelegate",
                "Permanent delegate extension",
                "Token-2022 permanent delegate — can steal tokens from ANY holder",
                RiskLevel.CRITICAL,
                "Permanent delegate can transfer tokens from any account without approval. CRITICAL.",
            ),
            (
                r"TransferFee|transfer_fee|TransferFeeConfig",
                "Transfer fee extension",
                "Token-2022 transfer fee — can be set to 100%",
                RiskLevel.HIGH,
                "Verify fee is immutable or bounded. Owner-controlled fee = rug vector.",
            ),
        ],
    }

    def __init__(self):
        super().__init__(
            AgentConfig(
                role=AgentRole.WEB3_SECURITY,
                name="web3_security",
                tools=["contract_scan", "pattern_match", "risk_calculate"],
                timeout_seconds=300.0,
            )
        )
        self.logger = logging.getLogger("secagents.web3_security")

    def base_system_prompt(self) -> str:
        return WEB3_SECURITY_PROMPT

    async def execute(self, task: dict) -> AgentOutput:
        """Execute smart contract auditing."""
        target_path = task.get("target_path", "")
        chain = task.get("chain", "evm").lower()

        if not target_path:
            return self._format_output(
                result={"error": "target_path required"},
                confidence=0.0,
                reasoning="No contract path to scan",
            )

        self.logger.info(f"Scanning {target_path} for {chain} vulnerabilities")

        try:
            findings = await self._scan_directory(target_path, chain)
            risk_score = self._calculate_risk_score(findings)
            verdict = self._get_verdict(risk_score)

            confidence = self._calculate_confidence(
                evidence_count=len(findings),
                max_evidence=15,
                base_confidence=0.7,
            )

            result = {
                "findings": [asdict(f) for f in findings],
                "risk_score": risk_score,
                "verdict": verdict,
                "chain": chain,
                "target": target_path,
            }

            return self._format_output(
                result=result,
                confidence=confidence,
                reasoning=f"Found {len(findings)} red flags in {chain} contracts. Verdict: {verdict}",
                metadata={"risk_score": risk_score, "verdict": verdict},
            )
        except Exception as e:
            self.logger.error(f"Web3 security scan failed: {str(e)}", exc_info=True)
            return self._format_output(
                result={"error": str(e)},
                confidence=0.0,
                reasoning="Scan execution failed",
            )

    async def _scan_directory(self, target_path: str, chain: str) -> List[Finding]:
        """Scan a directory or file for patterns."""
        path = Path(target_path)
        patterns = self.EVM_PATTERNS if chain == "evm" else self.SOLANA_PATTERNS
        ext = "*.sol" if chain == "evm" else "*.rs"

        findings = []
        files = []

        if path.is_file():
            files = [path]
        elif path.is_dir():
            files = list(path.rglob(ext))

        for f in files:
            if any(excl in f.parts for excl in ["node_modules", "lib", "test", "target"]):
                continue

            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()

                for category, category_patterns in patterns.items():
                    for regex, title, desc, risk, rec in category_patterns:
                        compiled = re.compile(regex)
                        for i, line in enumerate(lines, 1):
                            if compiled.search(line):
                                start = max(0, i - 3)
                                end = min(len(lines), i + 2)
                                snippet = "\n".join(lines[start:end])

                                findings.append(
                                    Finding(
                                        risk=risk,
                                        category=category,
                                        title=title,
                                        description=desc,
                                        file_path=str(f),
                                        line_number=i,
                                        code_snippet=snippet,
                                        recommendation=rec,
                                    )
                                )
            except Exception as e:
                self.logger.warning(f"Failed to read {f}: {e}")

        return self._deduplicate(findings)

    def _deduplicate(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings within 5 lines of each other in the same file."""
        seen: List[Finding] = []
        for f in findings:
            is_dup = False
            for s in seen:
                if (
                    f.title == s.title
                    and f.file_path == s.file_path
                    and abs(f.line_number - s.line_number) <= 5
                ):
                    is_dup = True
                    break
            if not is_dup:
                seen.append(f)
        return seen

    def _calculate_risk_score(self, findings: List[Finding]) -> int:
        weights = {
            RiskLevel.CRITICAL: 25,
            RiskLevel.HIGH: 10,
            RiskLevel.MEDIUM: 5,
            RiskLevel.LOW: 2,
            RiskLevel.INFO: 0,
        }
        return sum(weights.get(f.risk, 0) for f in findings)

    def _get_verdict(self, score: int) -> str:
        if score >= 50:
            return "CRITICAL RISK — DO NOT INTERACT"
        if score >= 25:
            return "HIGH RISK — LIKELY RUG VECTORS PRESENT"
        if score >= 10:
            return "MEDIUM RISK — MANUAL REVIEW NEEDED"
        if score >= 5:
            return "LOW RISK — MINOR CONCERNS"
        return "CLEAN — NO RED FLAGS DETECTED"
