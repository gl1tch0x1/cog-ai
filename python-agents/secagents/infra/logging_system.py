"""Structured audit logging for compliance (SOC 2 / ISO 27001)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock

LOG_DIR = Path.home() / ".secagents" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class AuditCategory(str, Enum):
    SCAN_START = "SCAN_START"
    SCAN_COMPLETE = "SCAN_COMPLETE"
    FINDING_CREATED = "FINDING_CREATED"
    VULNERABILITY_DETECTED = "VULNERABILITY_DETECTED"
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    AUTH_ATTEMPT = "AUTH_ATTEMPT"


class AuditLogger:
    _instance: AuditLogger | None = None
    _lock = Lock()

    def __init__(self):
        self._audit_file = LOG_DIR / "audit.jsonl"
        self._logger = logging.getLogger("secagents")
        if not self._logger.handlers:
            handler = logging.FileHandler(LOG_DIR / "secagents.log")
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    @classmethod
    def get_instance(cls) -> AuditLogger:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def audit(self, category: AuditCategory, message: str, **metadata) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category.value,
            "message": message,
            **metadata,
        }
        with self._lock:
            with open(self._audit_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        self._logger.info(f"[{category.value}] {message}")

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def error(self, msg: str) -> None:
        self._logger.error(msg)
        self.audit(AuditCategory.ERROR_OCCURRED, msg)

    def export_report(self) -> str:
        """Export audit trail as markdown."""
        if not self._audit_file.exists():
            return "# Audit Report\n\nNo entries."
        lines = ["# Audit Report\n", f"Generated: {datetime.now(timezone.utc).isoformat()}\n"]
        for raw in self._audit_file.read_text().strip().split("\n"):
            entry = json.loads(raw)
            lines.append(f"- **[{entry['category']}]** {entry['timestamp']}: {entry['message']}")
        return "\n".join(lines)
