#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          SecAgents — Automated Intelligence Updater              ║
║  "Synchronizing the Arsenal. Intelligence Re-established."      ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import subprocess
import sys
import shutil
from pathlib import Path

# ─── Terminal Aesthetic ──────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GRAY   = "\033[90m"
MAGENTA = "\033[35m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
WHITE  = "\033[97m"

PRE_INFO = f"{CYAN}󰋼{RESET}"
PRE_OK   = f"{GREEN}󰄬{RESET}"
PRE_FAIL = f"{RED}󰅚{RESET}"

BANNER = r"""
    __                     ____                               
   / /_  ________  _______/ __ \____ _      ______  ________ 
  / __ \/ ___/ _ \/ ___/ / / / __ `/ | /| / / __ \/ ___/ _ \
 / / / / /  /  __/ /__/ /_/ / /_/ /| |/ |/ / / / / /  /  __/
/_/ /_/_/   \___/\___/\____/\__,_/ |__/|__/_/ /_/_/   \___/ 
                                                              
         » FRAMEWORK SYNCHRONIZATION & INTELLIGENCE RECALL «
"""

def c(color: str, text: str) -> str:
    return f"{color}{text}{RESET}"

def info(msg: str): print(f"  {PRE_INFO} {c(CYAN, msg)}")
def ok(msg: str): print(f"  {PRE_OK} {c(GRAY, msg)}")
def error(msg: str): print(f"  {PRE_FAIL} {c(RED, msg)}")

def run(cmd: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), shell=True, text=True, capture_output=True)

def main():
    print(c(BOLD+MAGENTA, BANNER))
    
    root = Path(__file__).parent.resolve()
    
    # 1. Environment Validation
    if not shutil.which("git"):
        error("Uplink failed: Git binary not detected.")
        sys.exit(1)

    if not (root / ".git").exists():
        error("Uplink failed: Not a localized repository.")
        sys.exit(1)

    # 2. Synchronize with Origin
    info("Establishing connection to origin...")
    fetch = run("git fetch origin", root)
    if fetch.returncode != 0:
        error(f"Synchronization failed: {fetch.stderr.strip()}")
        sys.exit(1)

    # 3. Delta Analysis
    info("Analyzing local vs remote intelligence...")
    local_rev = run("git rev-parse HEAD", root).stdout.strip()
    try:
        remote_rev = run("git rev-parse @{u}", root).stdout.strip()
    except:
        error("Intelligence recall failed: Could not resolve upstream.")
        sys.exit(1)
    
    if local_rev == remote_rev:
        ok(f"Framework is synchronized (Rev: {local_rev[:7]})")
        try:
            choice = input(f"\n  {c(MAGENTA, '::')} Re-run deployment sequence to verify arsenal? [y/N]: ").lower()
        except: return
        if choice != 'y': return
    else:
        info("New intelligence detected. Synchronizing delta...")
        pull = run("git pull", root)
        if pull.returncode != 0:
            error("Synchronization collapsed. Conflict detected.")
            print(f"  {c(YELLOW, pull.stderr.strip())}")
            sys.exit(1)
        ok("New intelligence integrated successfully.")

    # 4. Deployment Sequence
    info("Initiating deployment sequence to arm modules...")
    try:
        # Pass through any args given to update.py to installer.py
        installer_args = sys.argv[1:]
        subprocess.run([sys.executable, "installer.py"] + installer_args, cwd=str(root))
    except Exception as e:
        error(f"Deployment sequence failed: {e}")
        sys.exit(1)

    print("\n" + c(MAGENTA, "━" * 65))
    ok("SYNCHRONIZATION COMPLETE. OPERATIONAL READINESS RESTORED.")
    print(c(MAGENTA, "━" * 65) + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{c(RED, 'Aborted.')}")
        sys.exit(130)
