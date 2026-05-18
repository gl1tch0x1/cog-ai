"""Two-tier caching: LLM response cache + scan result cache."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from threading import Lock

_CACHE_DIR = Path.home() / ".secagents" / "cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class LLMResponseCache:
    """Memory + disk cache for LLM API responses with TTL."""

    def __init__(self, ttl: int = 86400):
        self._mem: dict[str, tuple[float, str]] = {}
        self._ttl = ttl
        self._hits = 0
        self._lock = Lock()
        self._dir = _CACHE_DIR / "llm"
        self._dir.mkdir(exist_ok=True)

    def _key(self, system: str, user: str, model: str) -> str:
        raw = f"{system}:::{user}:::{model}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, system: str, user: str, model: str) -> str | None:
        k = self._key(system, user, model)
        with self._lock:
            if k in self._mem:
                ts, val = self._mem[k]
                if time.time() - ts < self._ttl:
                    self._hits += 1
                    return val
                del self._mem[k]
            # Check disk
            path = self._dir / f"{k}.json"
            if path.exists():
                data = json.loads(path.read_text())
                if time.time() - data["ts"] < self._ttl:
                    self._mem[k] = (data["ts"], data["val"])
                    self._hits += 1
                    return data["val"]
                path.unlink()
        return None

    def set(self, system: str, user: str, model: str, response: str) -> None:
        k = self._key(system, user, model)
        ts = time.time()
        with self._lock:
            self._mem[k] = (ts, response)
            path = self._dir / f"{k}.json"
            path.write_text(json.dumps({"ts": ts, "val": response}))

    def get_stats(self) -> dict:
        return {"entries": len(self._mem), "hits": self._hits}

    def clear_expired(self) -> int:
        removed = 0
        now = time.time()
        with self._lock:
            expired = [k for k, (ts, _) in self._mem.items() if now - ts >= self._ttl]
            for k in expired:
                del self._mem[k]
                p = self._dir / f"{k}.json"
                p.unlink(missing_ok=True)
                removed += 1
        return removed


class ScanResultCache:
    """Cache scan results keyed by target + content hash."""

    def __init__(self, ttl: int = 604800):
        self._ttl = ttl
        self._dir = _CACHE_DIR / "scans"
        self._dir.mkdir(exist_ok=True)

    def _key(self, target: str, content_hash: str) -> str:
        return hashlib.sha256(f"{target}:::{content_hash}".encode()).hexdigest()

    def get(self, target: str, content_hash: str) -> dict | None:
        path = self._dir / f"{self._key(target, content_hash)}.json"
        if path.exists():
            data = json.loads(path.read_text())
            if time.time() - data["ts"] < self._ttl:
                return data["result"]
            path.unlink()
        return None

    def set(self, target: str, content_hash: str, result: dict) -> None:
        path = self._dir / f"{self._key(target, content_hash)}.json"
        path.write_text(json.dumps({"ts": time.time(), "result": result}))


_llm_cache: LLMResponseCache | None = None
_scan_cache: ScanResultCache | None = None


def get_llm_cache() -> LLMResponseCache:
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LLMResponseCache()
    return _llm_cache


def get_scan_cache() -> ScanResultCache:
    global _scan_cache
    if _scan_cache is None:
        _scan_cache = ScanResultCache()
    return _scan_cache
