"""Module 6: Planner, specialist hiring, and horizontal scaling."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from secagents.core.orchestrator import Orchestrator, Intent, ExecutionGraph


@dataclass
class AgentSpec:
    name: str
    role: str
    handler: Callable[..., Awaitable[Any]] | None = None


# Specialist agents mapped to scan phases
DEFAULT_SPECIALISTS = [
    AgentSpec("port_scan", "Port Scan Agent"),
    AgentSpec("subdomain", "Subdomain Enumeration Agent"),
    AgentSpec("web_crawl", "Web Crawl Agent"),
    AgentSpec("sqli", "SQLi Agent"),
    AgentSpec("xss", "XSS Agent"),
    AgentSpec("ssrf", "SSRF Agent"),
    AgentSpec("idor", "IDOR Agent"),
    AgentSpec("validator", "Validator Agent"),
]


class ArmadaOrchestrator:
    """
    Decomposes missions into DAGs and dispatches specialist agents.
    Supports --workers N for parallel execution.
    """

    def __init__(self, workers: int = 4):
        self.workers = max(1, workers)
        self._orchestrator = Orchestrator()
        self._specialists: dict[str, AgentSpec] = {s.name: s for s in DEFAULT_SPECIALISTS}
        self._handlers: dict[str, Callable] = {}

    def register_handler(self, agent_name: str, handler: Callable[..., Awaitable[Any]]) -> None:
        self._handlers[agent_name] = handler
        if agent_name in self._specialists:
            self._specialists[agent_name].handler = handler

    def plan_mission(self, target: str, depth: str = "standard") -> ExecutionGraph:
        """Planner Agent: build DAG from high-level goal."""
        intent = Intent.SCAN
        context = {"target": target, "depth": depth}
        graph = self._orchestrator.decompose_intent(intent, context)

        # Route tasks to appropriate specialist agents based on action semantics
        action_routing = {
            "full_recon": "subdomain",
            "universal_scan": "web_crawl",
            "validate": "validator",
            "generate": "validator",
        }
        for task in graph.tasks:
            routed = action_routing.get(task.action)
            if routed and routed in self._specialists:
                task.agent = routed
            elif task.agent not in self._specialists:
                # Fallback: keep existing agent if registered, else use first available
                task.agent = next(iter(self._specialists), task.agent)
        return graph

    def hire_specialists(self, graph: ExecutionGraph) -> list[AgentSpec]:
        """Return specialist agents needed for this DAG."""
        needed = {t.agent for t in graph.tasks if t.agent}
        return [self._specialists[n] for n in needed if n in self._specialists]

    async def execute(self, graph: ExecutionGraph, context: dict) -> dict:
        """Execute DAG with worker pool parallelism."""
        results: dict[str, Any] = {"tasks": {}, "findings": []}
        sem = asyncio.Semaphore(self.workers)

        async def run_task(task_id: str, agent: str, action: str) -> None:
            async with sem:
                handler = self._handlers.get(agent)
                if handler:
                    out = await handler(context=context, action=action)
                else:
                    out = {"status": "skipped", "agent": agent, "reason": "no handler registered"}
                results["tasks"][task_id] = out
                if isinstance(out, dict) and "findings" in out:
                    results["findings"].extend(out["findings"])

        from secagents.core.orchestrator import TaskState

        max_rounds = len(graph.tasks) + 5
        rounds = 0
        while not graph.is_complete and rounds < max_rounds:
            ready = graph.ready_tasks
            if not ready:
                # Deadlock: pending tasks with unmet dependencies
                pending = [t for t in graph.tasks if t.state == TaskState.PENDING]
                for t in pending:
                    t.state = TaskState.FAILED
                break
            await asyncio.gather(*[run_task(t.id, t.agent, t.action) for t in ready])
            for t in ready:
                t.state = TaskState.DONE
            rounds += 1

        return results
