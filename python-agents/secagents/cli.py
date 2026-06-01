#!/usr/bin/env python3
"""
SecAgent CLI — autonomous offensive security platform.

Usage:
  python -m secagents scan --target example.com --depth standard
  python -m secagents vault --validate
  python -m secagents worker
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from secagents import __version__
from secagents.operational.integrity import check_os_security_updates, check_and_apply_tool_update
from secagents.vault.env_loader import Vault
from secagents.pipeline.runner import ScanPipeline
from secagents.infra.preflight import run_preflight, preflight_ok
from secagents.infra.scope import enforce_scope, ScopeViolationError
from secagents.agents.keyhacks import KeyhacksAgent
from secagents.whichllm.hardware import detect_hardware, setup_ollama, recommend_local_model


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        Vault(Path(".env")).load()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="secagent",
        description="SecAgent — Autonomous Offensive AI Framework (authorized testing only)",
    )
    p.add_argument("--version", action="version", version=f"SecAgent {__version__}")

    sub = p.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Run autonomous scan pipeline")
    scan.add_argument("--target", "-t", required=True, help="Target domain or URL")
    scan.add_argument(
        "--depth",
        choices=["quick", "standard", "deep"],
        default="standard",
        help="Scan depth",
    )
    scan.add_argument("--workers", "-w", type=int, default=4, help="Parallel agent workers")
    scan.add_argument("--skip-os-check", action="store_true", help="Skip OS security update check")
    scan.add_argument("--no-sandbox", action="store_true", help="Disable Docker sandbox (not recommended)")
    scan.add_argument("--no-arsenal", action="store_true", help="Skip secondary Arsenal heuristic probes")
    scan.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    scan.add_argument("--setup-local-llm", action="store_true", help="Install optimal Ollama model via whichllm")
    scan.add_argument("--results-dir", default="cog-ai-results", help="Output directory")

    vault = sub.add_parser("vault", help="Validate and display API key status")
    vault.add_argument("--validate", action="store_true", help="Probe keys with cheap API calls")
    vault.add_argument("--env", default=".env", help="Path to .env file")

    preflight = sub.add_parser("preflight", help="Run system preflight checks")
    preflight.add_argument("--skip-os-check", action="store_true")

    update = sub.add_parser("update", help="Check and apply tool updates (explicit only)")
    update.add_argument("--check-only", action="store_true")

    hardware = sub.add_parser("hardware", help="Detect hardware and recommend local LLM")
    hardware.add_argument("--install", action="store_true", help="Pull recommended Ollama model")

    keyhacks = sub.add_parser("keyhacks", help="Scan files for leaked API keys")
    keyhacks.add_argument("paths", nargs="+", help="Files or directories to scan")
    keyhacks.add_argument("--rate-limit", type=float, default=10.0, help="Max validations per minute")

    sub.add_parser("worker", help="Run Redis workflow worker (API scan dispatch)")

    return p


async def cmd_scan(args: argparse.Namespace) -> int:
    if args.insecure:
        os.environ["SECAGENT_VERIFY_SSL"] = "false"

    try:
        enforce_scope(args.target)
    except ScopeViolationError as e:
        print(f"⛔ {e}")
        return 2

    pipeline = ScanPipeline(
        target=args.target,
        depth=args.depth,
        workers=args.workers,
        use_sandbox=not args.no_sandbox,
        skip_os_check=args.skip_os_check,
        setup_local_llm=args.setup_local_llm,
        results_dir=Path(args.results_dir),
        arsenal_secondary=not args.no_arsenal,
    )
    print(f"\n🎯 SecAgent scan: {args.target} (depth={args.depth}, workers={args.workers})\n")
    try:
        results = await pipeline.run()
    except Exception as e:
        print(f"❌ Scan execution failed: {e}")
        return 2

    n = len(results.get("findings", []))
    print(f"\n✅ Mission complete — {n} validated finding(s)")
    if results.get("reports"):
        for fmt, path in results["reports"].items():
            print(f"   📄 {fmt}: {path}")
    return 0


async def cmd_vault(args: argparse.Namespace) -> int:
    v = Vault(env_path=Path(args.env))
    if args.validate:
        await v.validate_all()
    else:
        v.load()
        v.reports = []
        for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "SHODAN_API_KEY", "CHAOS_API_KEY", "LLM_API_KEYS"):
            val = os.environ.get(name, "")
            from secagents.vault.env_loader import KeyReport, KeyStatus, mask_secret
            status = KeyStatus.PRESENT if val else KeyStatus.MISSING
            v.reports.append(KeyReport(name, status, mask_secret(val) if val else ""))
    v.print_status()
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    if not args.skip_os_check:
        ok, msg = check_os_security_updates(skip=False)
        print(msg)
        if not ok:
            return 1
    results = run_preflight()
    for r in results:
        sym = "✓" if r.passed else "✗"
        print(f"  {sym} {r.name}: {r.message}")
    return 0 if preflight_ok(results) else 1


def cmd_update(args: argparse.Namespace) -> int:
    if args.check_only:
        from secagents.operational.integrity import check_tool_update
        r = check_tool_update()
        print(r.message)
        return 0
    _, msg = check_and_apply_tool_update()
    print(msg)
    return 0


def cmd_hardware(args: argparse.Namespace) -> int:
    profile = detect_hardware()
    print(f"Hardware: {profile.summary()}")
    _, model = recommend_local_model(profile)
    print(f"Recommended: ollama / {model}")
    if args.install:
        ok, msg = setup_ollama(model, pull=True)
        print(msg)
        return 0 if ok else 1
    return 0


async def cmd_keyhacks(args: argparse.Namespace) -> int:
    agent = KeyhacksAgent(requests_per_minute=args.rate_limit)
    paths: list[str] = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            paths.extend(str(f) for f in path.rglob("*") if f.is_file() and not any(part in f.parts for part in (".git", ".venv", ".next", "node_modules")))
        elif path.is_file():
            paths.append(str(path))
    
    if not paths:
        print("No files found to scan.")
        return 0

    findings = await agent.scan_paths(paths[:500])
    for f in findings:
        status = "LIVE" if f.valid else ("UNKNOWN" if f.valid is None else "DEAD")
        print(f"  [{status}] {f.service}: {f.key_masked} — {f.message} ({f.source})")
    return 0


def cmd_worker() -> int:
    from secagents.worker.runner import main as worker_main
    worker_main()
    return 0


def main() -> None:
    _load_env()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        sys.exit(asyncio.run(cmd_scan(args)))
    elif args.command == "vault":
        sys.exit(asyncio.run(cmd_vault(args)))
    elif args.command == "preflight":
        sys.exit(cmd_preflight(args))
    elif args.command == "update":
        sys.exit(cmd_update(args))
    elif args.command == "hardware":
        sys.exit(cmd_hardware(args))
    elif args.command == "keyhacks":
        sys.exit(asyncio.run(cmd_keyhacks(args)))
    elif args.command == "worker":
        sys.exit(cmd_worker())


if __name__ == "__main__":
    main()
