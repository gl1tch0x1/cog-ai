"""AI Gateway: multi-model routing, failover, circuit breaker, provider abstraction."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class TaskType(str, Enum):
    PLANNING = "planning"
    CODING = "coding"
    VALIDATION = "validation"
    SUMMARIZATION = "summarization"
    REASONING = "reasoning"
    CLASSIFICATION = "classification"
    TOOL_ORCHESTRATION = "tool_orchestration"


@dataclass
class ModelRoute:
    provider: str
    model: str
    cost_per_1k: float
    avg_latency_ms: float
    max_tokens: int = 4096
    task_types: list[TaskType] = field(default_factory=list)
    priority: int = 0  # lower = preferred


@dataclass
class CircuitState:
    failures: int = 0
    last_failure: float = 0
    open_until: float = 0

    @property
    def is_open(self) -> bool:
        return time.time() < self.open_until

    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= 5:
            self.open_until = time.time() + 60  # 60s cooldown

    def record_success(self):
        self.failures = 0
        self.open_until = 0


# Default routing table
DEFAULT_ROUTES: list[ModelRoute] = [
    ModelRoute("groq", "llama-3.1-70b-versatile", 0.001, 200, 8192,
               [TaskType.CLASSIFICATION, TaskType.SUMMARIZATION], priority=0),
    ModelRoute("openai", "gpt-4o-mini", 0.002, 400, 16384,
               [TaskType.SUMMARIZATION, TaskType.CLASSIFICATION, TaskType.CODING], priority=1),
    ModelRoute("openai", "gpt-4o", 0.010, 800, 128000,
               [TaskType.CODING, TaskType.TOOL_ORCHESTRATION, TaskType.PLANNING], priority=2),
    ModelRoute("anthropic", "claude-sonnet-4-20250514", 0.015, 1200, 200000,
               [TaskType.REASONING, TaskType.VALIDATION, TaskType.PLANNING], priority=2),
    ModelRoute("deepseek", "deepseek-chat", 0.002, 600, 64000,
               [TaskType.CODING, TaskType.REASONING], priority=1),
    ModelRoute("ollama", "llama3", 0.0, 500, 8192,
               [TaskType.CLASSIFICATION, TaskType.SUMMARIZATION], priority=3),
]

# Hint → TaskType mapping
HINT_MAP = {
    "fast": TaskType.CLASSIFICATION,
    "balanced": TaskType.CODING,
    "reasoning": TaskType.REASONING,
    "cheap": TaskType.SUMMARIZATION,
    "planning": TaskType.PLANNING,
    "validation": TaskType.VALIDATION,
}


class AIGateway:
    """Routes requests to optimal model based on task type, cost, latency, availability."""

    def __init__(self, routes: list[ModelRoute] | None = None):
        self.routes = routes or DEFAULT_ROUTES
        self._circuits: dict[str, CircuitState] = {}
        self._stats: dict[str, dict] = {}  # provider:model → {calls, tokens, latency_sum}

    def select_model(self, task_type: TaskType | str, optimize: str = "balanced") -> ModelRoute | None:
        """Select best model for task type. optimize: cost|speed|balanced."""
        if isinstance(task_type, str):
            task_type = HINT_MAP.get(task_type, TaskType.CLASSIFICATION)

        candidates = [
            r for r in self.routes
            if task_type in r.task_types and not self._is_circuit_open(r)
        ]
        if not candidates:
            # Fallback: any available model
            candidates = [r for r in self.routes if not self._is_circuit_open(r)]
        if not candidates:
            return None

        if optimize == "cost":
            candidates.sort(key=lambda r: r.cost_per_1k)
        elif optimize == "speed":
            candidates.sort(key=lambda r: r.avg_latency_ms)
        else:
            # Balanced: weighted score (lower is better)
            candidates.sort(key=lambda r: r.cost_per_1k * 100 + r.avg_latency_ms / 100 + r.priority)

        return candidates[0]

    def get_fallback_chain(self, task_type: TaskType | str) -> list[ModelRoute]:
        """Get ordered fallback chain for a task type."""
        if isinstance(task_type, str):
            task_type = HINT_MAP.get(task_type, TaskType.CLASSIFICATION)
        return sorted(
            [r for r in self.routes if task_type in r.task_types],
            key=lambda r: r.priority
        )

    def record_success(self, route: ModelRoute, latency_ms: float, tokens: int) -> None:
        key = f"{route.provider}:{route.model}"
        self._get_circuit(key).record_success()
        stats = self._stats.setdefault(key, {"calls": 0, "tokens": 0, "latency_sum": 0})
        stats["calls"] += 1
        stats["tokens"] += tokens
        stats["latency_sum"] += latency_ms
        # Update running average
        route.avg_latency_ms = stats["latency_sum"] / stats["calls"]

    def record_failure(self, route: ModelRoute) -> None:
        key = f"{route.provider}:{route.model}"
        self._get_circuit(key).record_failure()

    def _is_circuit_open(self, route: ModelRoute) -> bool:
        key = f"{route.provider}:{route.model}"
        return self._get_circuit(key).is_open

    def _get_circuit(self, key: str) -> CircuitState:
        if key not in self._circuits:
            self._circuits[key] = CircuitState()
        return self._circuits[key]

    def get_stats(self) -> dict:
        return {k: {**v, "avg_latency": v["latency_sum"] / max(v["calls"], 1)}
                for k, v in self._stats.items()}
