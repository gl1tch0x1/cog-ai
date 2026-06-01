#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          SecAgents — Automated Red Team Installer               ║
║  "Industrial Power. Elite Intelligence. Mission Ready."         ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import os
import platform
import secrets
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# ─── Terminal Aesthetic ──────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Offensive Palette
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
BLUE   = "\033[34m"
MAGENTA = "\033[35m"
CYAN   = "\033[36m"
WHITE  = "\033[97m"
GRAY   = "\033[90m"

# Status Prefixes
PRE_INFO = f"{CYAN}󰋼{RESET}"
PRE_OK   = f"{GREEN}󰄬{RESET}"
PRE_WARN = f"{YELLOW}󱈸{RESET}"
PRE_FAIL = f"{RED}󰅚{RESET}"
PRE_STEP = f"{MAGENTA}󱐋{RESET}"

IS_WIN = platform.system() == "Windows"

def c(color: str, text: str) -> str:
    if os.environ.get("NO_COLOR") or (IS_WIN and not os.environ.get("WT_SESSION") and not os.environ.get("TERM_PROGRAM")):
        return text
    return f"{color}{text}{RESET}"

# ─── ASCII ARSENAL ───────────────────────────────────────────────────────────
BANNER = r"""
    __                     ____                               
   / /_  ________  _______/ __ \____ _      ______  ________ 
  / __ \/ ___/ _ \/ ___/ / / / __ `/ | /| / / __ \/ ___/ _ \
 / / / / /  /  __/ /__/ /_/ / /_/ /| |/ |/ / / / / /  /  __/
/_/ /_/_/   \___/\___/\____/\__,_/ |__/|__/_/ /_/_/   \___/ 
                                                              
         » AUTONOMOUS OFFENSIVE INTELLIGENCE FRAMEWORK «
          [ V0.3.0-DEV | Red Team Deployment Engine ]
"""

# ─── Paths ───────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.resolve()
VENV_DIR    = ROOT / ".venv"
PYTHON_AGENTS = ROOT / "python-agents"
API_DIR     = ROOT / "api"
ENV_FILE    = ROOT / ".env"
MIGRATION   = ROOT / "api" / "migrations" / "001_initial.sql"

PYTHON_EXEC = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("python.exe" if IS_WIN else "python"))
PIP_EXEC    = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("pip.exe" if IS_WIN else "pip"))
PYTEST_EXEC = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("pytest.exe" if IS_WIN else "pytest"))

# ─── Execution Logic ──────────────────────────────────────────────────────────
_step = 0
_errors: list[str] = []

def step(title: str) -> None:
    global _step
    _step += 1
    print(f"\n{c(MAGENTA, '::')} {c(BOLD+WHITE, title.upper())} {c(GRAY, '— phase ' + str(_step))}")
    print(c(MAGENTA, "━" * 65))

def ok(msg: str) -> None:
    print(f"  {PRE_OK} {c(GRAY, msg)}")

def warn(msg: str) -> None:
    print(f"  {PRE_WARN} {c(YELLOW, msg)}")

def fail(msg: str) -> None:
    print(f"  {PRE_FAIL} {c(RED, msg)}")
    _errors.append(msg)

def info(msg: str) -> None:
    print(f"  {PRE_INFO} {c(CYAN, msg)}")

def run(cmd: list[str], cwd: Optional[Path] = None, capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, capture_output=capture, text=True, check=check
    )

# ═══════════════════════════════════════════════════════════════════════
#  OPERATIONAL PHASES
# ═══════════════════════════════════════════════════════════════════════

def run_preflight(args: argparse.Namespace) -> bool:
    step("Preflight Reconnaissance")
    
    # Python Check
    v = sys.version_info
    if v >= (3, 11):
        ok(f"Runtime: Python {v.major}.{v.minor}.{v.micro} [COMPATIBLE]")
    else:
        fail(f"Runtime: Python {v.major}.{v.minor} [INCOMPATIBLE - 3.11+ REQUIRED]")
        return False

    # Disk Check
    try:
        total, used, free = shutil.disk_usage(ROOT)
        free_gb = free / (1024**3)
        if free_gb >= 2.0:
            ok(f"Storage: {free_gb:.1f} GB Available [OPTIMAL]")
        else:
            warn(f"Storage: {free_gb:.1f} GB [LOW - 2GB+ RECOMMENDED]")
    except: pass

    # Tools Check
    for tool, name in [("git", "Git"), ("docker", "Docker Engine"), ("node", "Node.js"), ("rustc", "Rust Compiler")]:
        path = shutil.which(tool)
        if path: ok(f"Binary: {name} detected at {path}")
        else: 
            if tool == "rustc":
                warn(f"Binary: {name} not found. Some Python packages may fail to build from source.")
            else:
                warn(f"Binary: {name} not found in PATH")

    # Network
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3).close()
        ok("Network: Uplink established [CONNECTED]")
    except:
        warn("Network: Uplink unstable [OFFLINE MODE]")
    
    return True

def deploy_environment() -> bool:
    step("Environment Hardening")
    if VENV_DIR.exists():
        info("Encryption tunnel (venv) already exists. Re-establishing connection...")
    else:
        info("Initializing isolated execution tunnel (venv)...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
            ok("Isolated tunnel created successfully.")
        except Exception as e:
            fail(f"Tunnel collapse: {e}")
            return False
    
    info("Upgrading deployment tools (pip, wheel)...")
    try:
        run([PYTHON_EXEC, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel", "--quiet"])
        ok("Tools hardened.")
    except: pass
    return True

def install_arsenal(args: argparse.Namespace) -> bool:
    step("Arming The Arsenal")
    
    packages = [
        ("Core Agents", PYTHON_AGENTS, ".[dev,browser]"),
        ("Orchestrator API", API_DIR, ".[dev]"),
    ]

    for name, path, extras in packages:
        if not path.exists(): continue
        info(f"Loading {name} modules...")
        try:
            # We use --prefer-binary to avoid building from source (which requires Rust)
            # especially if we are just running the Docker stack.
            run([PIP_EXEC, "install", "--prefer-binary", "-e", extras], cwd=path)
            ok(f"{name} armed and ready.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""
            if "pydantic-core" in stderr and "Rust" in stderr:
                msg = f"{name} failed to install: pydantic-core requires Rust to build."
                if args.docker:
                    warn(f"{msg} (Non-fatal in Docker mode, continuing...)")
                else:
                    fail(f"{msg} Hint: Install Rust (https://rustup.rs/) or use --docker.")
                    return False
            else:
                msg = f"Module load failed: {stderr[:200] if stderr else e}"
                if args.docker:
                    warn(f"{msg} (Non-fatal in Docker mode, continuing...)")
                else:
                    fail(msg)
                    return False

    info("Installing telemetry and UI enhancements (rich, typer)...")
    try:
        run([PIP_EXEC, "install", "rich", "typer", "pytest-cov", "--quiet"])
        ok("UI enhancements and test plugins loaded.")
    except: pass
    return True

def configure_intel() -> bool:
    step("Intel Configuration")
    if ENV_FILE.exists():
        warn("Intel manifest (.env) already exists. Skipping generation.")
        return True

    info("Generating secure operational keys...")
    db_pass = secrets.token_urlsafe(24)
    jwt_sec = secrets.token_urlsafe(48)
    
    content = f"""# SecAgent Offensive Intel Manifest
DB_PASSWORD={db_pass}
DATABASE_URL=postgresql+asyncpg://secagents:{db_pass}@localhost:5432/secagents
REDIS_URL=redis://localhost:6379/0
JWT_SECRET={jwt_sec}
ALLOWED_DOMAINS=example.com,*.example.com
# LLM KEYS
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
"""
    ENV_FILE.write_text(content)
    ok(f"Operational manifest written to {ENV_FILE}")
    info("REMINDER: Inject your API keys into .env before mission start.")
    return True

def start_docker_stack(args: argparse.Namespace) -> bool:
    step("Deploying Docker Operations")
    
    docker_bin = shutil.which("docker")
    if not docker_bin:
        fail("Docker Engine not found. Operation scrubbed.")
        return False

    # Check for docker compose
    compose_cmd = ["docker", "compose"]
    try:
        run(["docker", "compose", "version"], capture=True)
    except:
        if shutil.which("docker-compose"):
            compose_cmd = ["docker-compose"]
        else:
            fail("Docker Compose not found. Operation scrubbed.")
            return False

    info("Igniting Docker containers and building images...")
    try:
        # Use longer timeout for build
        subprocess.run(compose_cmd + ["up", "-d", "--build"], cwd=ROOT, check=True)
        ok("Docker operational stack is hot.")
    except Exception as e:
        fail(f"Docker ignition failure: {e}")
        return False

    return True

def run_tests(args: argparse.Namespace) -> bool:
    step("Operational Integrity Tests")
    
    if not Path(PYTEST_EXEC).exists():
        warn("Test runner not found in tunnel. Skipping.")
        return True

    info("Executing unit tests...")
    try:
        # We try to run with coverage, but fallback if it fails
        cmd = [PYTEST_EXEC, "tests/unit/", "-v", "--tb=short"]
        result = run(cmd, cwd=ROOT, check=False)
        if result.returncode == 0:
            ok("Integrity check passed.")
            return True
        else:
            warn("Some operational checks failed.")
            return False
    except Exception as e:
        warn(f"Test sequence error: {e}")
        return False

def print_mission_briefing(success: bool) -> None:
    print("\n" + c(MAGENTA, "━" * 65))
    if success:
        print(c(BOLD+GREEN, "  [+] MISSION READY: SECAGENT DEPLOYED SUCCESSFULLY"))
    else:
        print(c(BOLD+YELLOW, "  [!] DEPLOYMENT COMPLETE WITH MINOR ANOMALIES"))

    print(f"\n{c(BOLD+WHITE, 'OPERATIONAL COMMANDS:')}")
    
    act = "source .venv/bin/activate" if not IS_WIN else r".venv\Scripts\activate"
    
    print(f"  {c(CYAN, '1.')} Hardening check:      {c(GRAY, 'cat .env')}")
    print(f"  {c(CYAN, '2.')} Enter tunnel:        {c(GRAY, act)}")
    print(f"  {c(CYAN, '3.')} Initialize scan:     {c(GRAY, 'secagent scan -t example.com')}")
    print(f"  {c(CYAN, '4.')} Breach report:       {c(GRAY, 'ls cog-ai-results/')}")
    
    print("\n" + c(MAGENTA, "━" * 65))
    print(c(DIM+ITALIC+WHITE, "  'Industrial Power. Elite Intelligence. Mission Ready.'"))
    print(c(MAGENTA, "━" * 65) + "\n")

def main() -> int:
    print(c(BOLD+GREEN, BANNER))
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker", action="store_true", help="Deploy with Docker stack")
    parser.add_argument("--no-test", action="store_true", help="Skip integrity tests")
    parser.add_argument("--ci", action="store_true")
    args = parser.parse_args()

    phases = [
        ("Preflight", lambda: run_preflight(args)),
        ("Environment", deploy_environment),
        ("Arsenal", lambda: install_arsenal(args)),
        ("Intel", configure_intel)
    ]

    if args.docker:
        phases.append(("Docker", lambda: start_docker_stack(args)))

    if not args.no_test:
        phases.append(("Tests", lambda: run_tests(args)))

    success = True
    for name, phase in phases:
        try:
            if not phase(): 
                success = False
                if not args.docker: break # Fail fast if not in docker mode
        except KeyboardInterrupt:
            print(f"\n{c(RED, 'Aborted.')}"); return 130
        except Exception as e:
            fail(f"Phase {name} crash: {e}"); success = False

    print_mission_briefing(success and not _errors)
    return 0 if (success and not _errors) else 1

if __name__ == "__main__":
    sys.exit(main())
