"""Module 4: Hermetic learning loop — SQLite memory for engagements."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MemoryEntry:
    id: int
    kind: str  # exploit_success, exploit_failure, skill, note
    target: str
    payload: dict
    created_at: float


class HermesMemory:
    """Persistent store for exploits, failures, and generated skills."""

    def __init__(self, db_path: str | Path = "cog-ai-results/hermes/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    target TEXT,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    language TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
            """)

    def log_success(self, target: str, exploit_type: str, details: dict) -> int:
        return self._insert("exploit_success", target, {"type": exploit_type, **details})

    def log_failure(self, target: str, exploit_type: str, reason: str, details: dict | None = None) -> int:
        return self._insert(
            "exploit_failure",
            target,
            {"type": exploit_type, "reason": reason, **(details or {})},
        )

    def _insert(self, kind: str, target: str, payload: dict) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO memories (kind, target, payload, created_at) VALUES (?, ?, ?, ?)",
                (kind, target, json.dumps(payload), time.time()),
            )
            return cur.lastrowid or 0

    def save_skill(self, name: str, source: str, language: str = "python") -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO skills (name, language, source, created_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET source=excluded.source""",
                (name, language, source, time.time()),
            )

    def get_skills(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT name, language, source FROM skills ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def query_similar_failures(self, exploit_type: str, limit: int = 5) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT payload FROM memories
                   WHERE kind='exploit_failure' AND payload LIKE ?
                   ORDER BY created_at DESC LIMIT ?""",
                (f'%"type": "{exploit_type}"%', limit),
            ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def export_json(self, path: Path) -> None:
        with self._conn() as conn:
            memories = [
                dict(r)
                for r in conn.execute("SELECT kind, target, payload, created_at FROM memories").fetchall()
            ]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"memories": memories}, indent=2))
