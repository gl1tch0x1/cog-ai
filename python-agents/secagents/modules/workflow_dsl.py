"""YAML workflow DSL: declarative security pipelines with variable interpolation."""

from __future__ import annotations

import json
import re
from typing import Any


def load_workflow(path: str) -> dict:
    """Load and validate a YAML or JSON workflow definition."""
    with open(path) as f:
        content = f.read()
    # Try JSON first, then YAML
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            import yaml
            return yaml.safe_load(content)
        except ImportError:
            raise ImportError("Install pyyaml: pip install pyyaml")


def resolve_variables(template: str, context: dict) -> str:
    """Resolve ${variable.path} references in strings."""
    def replacer(match):
        path = match.group(1)
        value = context
        for key in path.split("."):
            if isinstance(value, dict):
                value = value.get(key, "")
            else:
                return ""
        return str(value) if value else ""

    return re.sub(r"\$\{([^}]+)\}", replacer, template)


class WorkflowDSL:
    """Execute YAML-defined security workflows."""

    def __init__(self):
        self.context: dict[str, Any] = {}

    async def execute(self, workflow: dict, executors: dict) -> dict:
        """Run a workflow definition with provided step executors."""
        results = {}
        steps = workflow.get("steps", [])

        for step in steps:
            step_type = step.get("type", "task")
            name = step.get("name", "unnamed")

            if step_type == "task":
                result = await self._run_task(step, executors)
            elif step_type == "parallel":
                result = await self._run_parallel(step, executors)
            elif step_type == "conditional":
                result = await self._run_conditional(step, executors)
            else:
                result = {"error": f"unknown step type: {step_type}"}

            results[name] = result
            self.context[f"steps.{name}"] = result

        return results

    async def _run_task(self, step: dict, executors: dict) -> Any:
        agent = step.get("agent", "")
        action = step.get("action", "")
        config = step.get("config", {})

        # Resolve variables in config
        resolved = {}
        for k, v in config.items():
            resolved[k] = resolve_variables(str(v), self.context) if isinstance(v, str) else v

        executor = executors.get(agent)
        if executor:
            return await executor(action, resolved)
        return {"error": f"no executor for agent: {agent}"}

    async def _run_parallel(self, step: dict, executors: dict) -> list:
        import asyncio
        tasks = step.get("tasks", [])
        coros = [self._run_task(t, executors) for t in tasks]
        return await asyncio.gather(*coros, return_exceptions=True)

    async def _run_conditional(self, step: dict, executors: dict) -> Any:
        condition = step.get("condition", "")
        resolved = resolve_variables(condition, self.context)
        if resolved and resolved.lower() not in ("", "false", "0", "none"):
            return await self._run_task(step.get("then", {}), executors)
        elif "else" in step:
            return await self._run_task(step["else"], executors)
        return None
