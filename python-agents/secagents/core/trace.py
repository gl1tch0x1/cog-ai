from __future__ import annotations

import time
import uuid
import os
import sys
from dataclasses import dataclass, field
from threading import Lock
from loguru import logger

# Configure Loguru for Agents
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "json")

logger.remove()
if LOG_FORMAT == "json":
    logger.add(sys.stdout, level=LOG_LEVEL, serialize=True)
else:
    logger.add(sys.stdout, level=LOG_LEVEL)


@dataclass
class Span:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    parent_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float = 0
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    status: str = "running"
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    def finish(self, status: str = "ok", **meta) -> None:
        self.end_time = time.time()
        self.status = status
        self.metadata.update(meta)


class Tracer:
    """Distributed tracing for agent execution pipelines."""

    def __init__(self):
        self._spans: list[Span] = []
        self._lock = Lock()
        self._token_total = {"in": 0, "out": 0}

    def start_span(self, name: str, parent_id: str | None = None, **meta) -> Span:
        span = Span(name=name, parent_id=parent_id, metadata=meta)
        with self._lock:
            self._spans.append(span)

        logger.info(
            "Span started", span_id=span.id, span_name=span.name, parent_id=span.parent_id, **meta
        )
        return span

    def finish_span(
        self, span: Span, status: str = "ok", tokens_in: int = 0, tokens_out: int = 0
    ) -> None:
        span.finish(status=status)
        span.tokens_in = tokens_in
        span.tokens_out = tokens_out
        with self._lock:
            self._token_total["in"] += tokens_in
            self._token_total["out"] += tokens_out

        logger.info(
            "Span finished",
            span_id=span.id,
            span_name=span.name,
            status=span.status,
            duration_ms=round(span.duration_ms, 2),
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

    def get_trace(self, root_id: str | None = None) -> list[dict]:
        """Get trace tree. If root_id given, only that subtree."""
        with self._lock:
            spans = (
                self._spans
                if not root_id
                else [s for s in self._spans if s.id == root_id or s.parent_id == root_id]
            )
            return [
                {
                    "id": s.id,
                    "name": s.name,
                    "parent": s.parent_id,
                    "duration_ms": round(s.duration_ms, 1),
                    "status": s.status,
                    "tokens": {"in": s.tokens_in, "out": s.tokens_out},
                    "model": s.model,
                    "metadata": s.metadata,
                }
                for s in spans
            ]

    @property
    def total_tokens(self) -> dict:
        return dict(self._token_total)

    @property
    def total_latency_ms(self) -> float:
        with self._lock:
            return sum(s.duration_ms for s in self._spans if s.end_time > 0)

    @property
    def span_count(self) -> int:
        return len(self._spans)

    def summary(self) -> dict:
        with self._lock:
            completed = [s for s in self._spans if s.end_time > 0]
            failed = [s for s in completed if s.status != "ok"]
            return {
                "total_spans": len(self._spans),
                "completed": len(completed),
                "failed": len(failed),
                "total_tokens": self._token_total,
                "avg_latency_ms": round(
                    sum(s.duration_ms for s in completed) / max(len(completed), 1), 1
                ),
            }

    def reset(self) -> None:
        with self._lock:
            self._spans.clear()
            self._token_total = {"in": 0, "out": 0}
