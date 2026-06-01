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

PYTHON_EXEC = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("python.exe" if IS_WIN else "python"))
PIP_EXEC    = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("pip.exe" if IS_WIN else "pip"))

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

def run(cmd: list[str], cwd: Optional[Path] = None, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, capture_output=capture, text=True, check=True
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
    for tool, name in [("git", "Git"), ("docker", "Docker Engine"), ("node", "Node.js")]:
        path = shutil.which(tool)
        if path: ok(f"Binary: {name} detected at {path}")
        else: warn(f"Binary: {name} not found in PATH")

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

def install_arsenal() -> bool:
    step("Arming The Arsenal")
    
    packages = [
        ("Core Agents", PYTHON_AGENTS, ".[dev,browser]"),
        ("Orchestrator API", API_DIR, ".[dev]"),
    ]

    for name, path, extras in packages:
        if not path.exists(): continue
        info(f"Loading {name} modules...")
        try:
            run([PIP_EXEC, "install", "-e", extras], cwd=path)
            ok(f"{name} armed and ready.")
        except subprocess.CalledProcessError as e:
            fail(f"Module load failed: {e.stderr[:200] if e.stderr else e}")
            return False

    info("Installing telemetry and UI enhancements (rich, typer)...")
    try:
        run([PIP_EXEC, "install", "rich", "typer", "--quiet"])
        ok("UI enhancements loaded.")
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
    parser.add_argument("--ci", action="store_true")
    args = parser.parse_args()

    phases = [
        run_preflight,
        deploy_environment,
        install_arsenal,
        configure_intel
    ]

    success = True
    for phase in phases:
        try:
            if phase == run_preflight:
                if not phase(args):
                    success = False; break
            else:
                if not phase(): success = False
        except KeyboardInterrupt:
            print(f"\n{c(RED, 'Aborted.')}"); return 130
        except Exception as e:
            fail(f"Phase crash: {e}"); success = False

    print_mission_briefing(success and not _errors)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
