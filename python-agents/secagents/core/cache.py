"""Smart Caching System: Thread-safe LRU cache with TTL expiration."""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from typing import Any, Optional


class SmartCache:
    """Thread-safe LRU Cache with TTL support for scan artifacts and responses."""

    def __init__(self, maxsize: int = 1000, default_ttl: int = 3600):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    @staticmethod
    def hash_key(key_input: Any) -> str:
        """Generate a deterministic SHA-256 key from arbitrary input."""
        if isinstance(key_input, (dict, list)):
            raw = json.dumps(key_input, sort_keys=True)
        else:
            raw = str(key_input)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: Any) -> Optional[Any]:
        """Retrieve item from cache if present and not expired."""
        k = self.hash_key(key)
        if k not in self._cache:
            return None

        val, expire_at = self._cache[k]
        if time.time() > expire_at:
            del self._cache[k]
            return None

        self._cache.move_to_end(k)
        return val

    def set(self, key: Any, value: Any, ttl: Optional[int] = None) -> str:
        """Store item in cache with TTL and LRU eviction."""
        k = self.hash_key(key)
        expire_at = time.time() + (ttl if ttl is not None else self.default_ttl)

        if k in self._cache:
            self._cache.move_to_end(k)
        self._cache[k] = (value, expire_at)

        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

        return k

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def stats(self) -> dict[str, Any]:
        """Return cache status and count."""
        now = time.time()
        active = sum(1 for _, expire_at in self._cache.values() if expire_at > now)
        return {
            "total_entries": len(self._cache),
            "active_entries": active,
            "maxsize": self.maxsize,
            "default_ttl": self.default_ttl,
        }
