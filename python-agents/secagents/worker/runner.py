"""Background worker: Redis secagents_workflows → ScanPipeline."""

from __future__ import annotations

import asyncio
import json
import os
import sys

from secagents.pipeline.runner import ScanPipeline
from secagents.infra.scope import ScopeViolationError, enforce_scope
from secagents.vault.env_loader import Vault


async def handle_workflow(message: dict) -> dict:
    config = message.get("config") or {}
    target = config.get("target") or config.get("domain")
    if not target:
        target_id = message.get("target_id")
        raise ValueError(f"No target in workflow config (target_id={target_id})")

    enforce_scope(str(target))
    pipeline = ScanPipeline(
        target=str(target),
        depth=config.get("depth", "standard"),
        workers=int(config.get("workers", 4)),
        use_sandbox=config.get("use_sandbox", True),
        skip_os_check=config.get("skip_os_check", False),
    )
    return await pipeline.run()


async def run_worker(redis_url: str | None = None, channel: str = "secagents_workflows") -> None:
    try:
        import redis.asyncio as aioredis
    except ImportError as e:
        raise SystemExit("redis package required: pip install redis") from e

    Vault().load()
    url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    client = aioredis.from_url(url)
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)
    print(f"SecAgent worker listening on {channel} ({url})")

    async for raw in pubsub.listen():
        if raw["type"] != "message":
            continue
        try:
            payload = json.loads(raw["data"])
            trace = payload.get("trace_id", "?")
            print(f"[worker] workflow trace_id={trace}")
            results = await handle_workflow(payload)
            print(f"[worker] complete findings={len(results.get('findings', []))}")
        except ScopeViolationError as e:
            print(f"[worker] scope blocked: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[worker] error: {e}", file=sys.stderr)


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
