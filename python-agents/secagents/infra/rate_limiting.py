"""Token-bucket rate limiter with per-provider limits."""

from __future__ import annotations

import time
from threading import Lock

PROVIDER_LIMITS: dict[str, dict] = {
    "openai": {"capacity": 3500, "refill_per_sec": 58},
    "anthropic": {"capacity": 100, "refill_per_sec": 1.67},
    "groq": {"capacity": 30, "refill_per_sec": 0.5},
    "ollama": {"capacity": 100, "refill_per_sec": 1.67},
    "deepseek": {"capacity": 50, "refill_per_sec": 0.83},
    "gemini": {"capacity": 60, "refill_per_sec": 1.0},
    "xai": {"capacity": 60, "refill_per_sec": 1.0},
}


class TokenBucket:
    def __init__(self, capacity: float, refill_per_sec: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_per_sec = refill_per_sec
        self.last_refill = time.time()
        self._lock = Lock()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_and_consume(self, tokens: int = 1) -> None:
        while True:
            if self.consume(tokens):
                return
            time.sleep(0.5)

    def status(self) -> dict:
        with self._lock:
            self._refill()
            return {
                "available": round(self.tokens, 1),
                "capacity": self.capacity,
                "utilization": round((1 - self.tokens / self.capacity) * 100, 1),
            }


class RateLimiter:
    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        for provider, cfg in PROVIDER_LIMITS.items():
            self._buckets[provider] = TokenBucket(cfg["capacity"], cfg["refill_per_sec"])

    def check(self, provider: str) -> None:
        """Block until rate limit allows a request."""
        bucket = self._buckets.get(provider)
        if bucket:
            bucket.wait_and_consume()

    def status(self, provider: str) -> dict:
        bucket = self._buckets.get(provider)
        return bucket.status() if bucket else {"error": "unknown provider"}

    def all_status(self) -> dict[str, dict]:
        return {p: b.status() for p, b in self._buckets.items()}


_instance: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _instance
    if _instance is None:
        _instance = RateLimiter()
    return _instance
