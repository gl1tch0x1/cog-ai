"""Persistent memory graph for cross-phase data sharing."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from threading import Lock
from typing import Any


class MemoryGraph:
    """Lightweight directed graph with indexed queries and atomic persistence."""

    def __init__(self, persist_path: str | None = None):
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, str]] = []
        self._index: dict[str, set[str]] = {}
        self._lock = Lock()
        self._path = Path(persist_path) if persist_path else None
        if self._path and self._path.exists():
            self._load()

    def add_node(self, node_id: str, **data) -> None:
        with self._lock:
            self._nodes[node_id] = data
            for k, v in data.items():
                key = f"{k}:{v}"
                self._index.setdefault(key, set()).add(node_id)

    def add_edge(self, source: str, target: str, relation: str) -> None:
        with self._lock:
            self._edges.append({"source": source, "target": target, "relation": relation})

    def query(self, **filters) -> list[dict]:
        """Query nodes by attribute filters using index."""
        with self._lock:
            if not filters:
                return list(self._nodes.values())
            first_key = next(iter(filters))
            first_val = filters[first_key]
            candidates = self._index.get(f"{first_key}:{first_val}", set())
            results = []
            for nid in candidates:
                node = self._nodes.get(nid, {})
                if all(node.get(k) == v for k, v in filters.items()):
                    results.append({"id": nid, **node})
            return results

    def neighbors(self, node_id: str, relation: str | None = None) -> list[str]:
        with self._lock:
            return [
                e["target"]
                for e in self._edges
                if e["source"] == node_id and (relation is None or e["relation"] == relation)
            ]

    def save(self) -> None:
        if not self._path:
            return
        with self._lock:
            data = {"nodes": self._nodes, "edges": self._edges}
            # Atomic write
            tmp = tempfile.NamedTemporaryFile(
                mode="w", dir=self._path.parent, delete=False, suffix=".tmp"
            )
            json.dump(data, tmp, default=str)
            tmp.close()
            Path(tmp.name).replace(self._path)

    def _load(self) -> None:
        data = json.loads(self._path.read_text())
        self._nodes = data.get("nodes", {})
        self._edges = data.get("edges", [])
        for nid, node_data in self._nodes.items():
            for k, v in node_data.items():
                self._index.setdefault(f"{k}:{v}", set()).add(nid)

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)
