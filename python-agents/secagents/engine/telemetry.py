"""Telemetry collector for agent actions, tool calls, and errors."""

from __future__ import annotations

import gzip
import json
import time
from pathlib import Path
from threading import Lock


class TelemetryCollector:
    def __init__(self, output_dir: str | None = None, max_size_mb: float = 10.0):
        self._entries: list[dict] = []
        self._lock = Lock()
        self._start = time.time()
        self._max_bytes = int(max_size_mb * 1024 * 1024)
        self._dir = Path(output_dir) if output_dir else Path.home() / ".secagents" / "telemetry"
        self._dir.mkdir(parents=True, exist_ok=True)

    def record_action(self, agent: str, action: str, **metadata) -> None:
        self._add("action", agent=agent, action=action, **metadata)

    def record_tool_call(self, tool: str, duration_ms: float, success: bool) -> None:
        self._add("tool_call", tool=tool, duration_ms=duration_ms, success=success)

    def record_error(self, source: str, error: str) -> None:
        self._add("error", source=source, error=error)

    def _add(self, event_type: str, **data) -> None:
        entry = {"type": event_type, "ts": time.time(), **data}
        with self._lock:
            self._entries.append(entry)

    def save(self) -> Path:
        """Persist telemetry to disk. Rotates if over max size."""
        path = self._dir / "telemetry.jsonl"
        if path.exists() and path.stat().st_size > self._max_bytes:
            self._rotate(path)

        with self._lock:
            data = {
                "duration_sec": round(time.time() - self._start, 2),
                "entries": self._entries,
            }
            with open(path, "a") as f:
                f.write(json.dumps(data) + "\n")
            saved = path
            self._entries.clear()
        return saved

    def _rotate(self, path: Path) -> None:
        rotated = path.with_suffix(f".{int(time.time())}.jsonl.gz")
        with open(path, "rb") as f_in, gzip.open(rotated, "wb") as f_out:
            f_out.write(f_in.read())
        path.unlink()

    @property
    def entry_count(self) -> int:
        return len(self._entries)
