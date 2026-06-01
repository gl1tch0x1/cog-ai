#!/usr/bin/env python3
"""
SecAgents — Automated Updater
Automates pulling latest changes from GitHub and re-syncing the environment.
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

# Terminal colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

def info(msg): print(f"{CYAN}·{RESET} {msg}")
def ok(msg): print(f"{GREEN}✓{RESET} {msg}")
def warn(msg): print(f"{YELLOW}⚠{RESET} {msg}")
def error(msg): print(f"{RED}✗{RESET} {msg}")

def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, shell=True, text=True, capture_output=True)

def main():
    print(f"\n{BOLD}SecAgents Update Utility{RESET}")
    print("=" * 30)

    root = Path(__file__).parent.resolve()
    
    # 1. Check for Git
    if not shutil.which("git"):
        error("Git not found. Cannot update via repository.")
        sys.exit(1)

    # 2. Check if it's a git repo
    if not (root / ".git").exists():
        error("Not a git repository. Please clone from GitHub to use the updater.")
        sys.exit(1)

    # 3. Fetch latest
    info("Fetching latest changes from origin...")
    fetch = run("git fetch origin", cwd=root)
    if fetch.returncode != 0:
        error(f"Failed to fetch: {fetch.stderr}")
        sys.exit(1)

    # 4. Check for updates
    info("Checking for updates...")
    local_rev = run("git rev-parse HEAD", cwd=root).stdout.strip()
    remote_rev = run("git rev-parse @{u}", cwd=root).stdout.strip()
    
    if local_rev == remote_rev:
        ok("SecAgents is already up to date (Rev: " + local_rev[:7] + ").")
        # Offer to re-run installer anyway
        try:
            choice = input("\nRe-run installer to ensure dependencies are synced? [y/N]: ").lower()
        except (EOFError, KeyboardInterrupt):
            return
        if choice != 'y':
            return
    else:
        info("New updates found. Pulling changes...")
        pull = run("git pull", cwd=root)
        if pull.returncode != 0:
            error(f"Failed to pull changes: {pull.stderr}")
            warn("You might have local changes that conflict with the update.")
            sys.exit(1)
        ok("Successfully pulled latest changes.")

    # 5. Run installer
    info("Running installer to sync dependencies...")
    # Detect if we should use --docker based on existing .env or previous choice
    # For simplicity, we run the installer interactively
    try:
        subprocess.run([sys.executable, "installer.py"], cwd=root)
    except Exception as e:
        error(f"Failed to run installer: {e}")
        sys.exit(1)

    ok("Update complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nUpdate cancelled.")
        sys.exit(130)
