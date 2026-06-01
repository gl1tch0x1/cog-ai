#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          SecAgents — Intelligence Recall Utility                 ║
║       "Synchronizing the Arsenal. Redefining the Edge."         ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import subprocess
import sys
import shutil
import time
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
    from rich.text import Text
    from rich.theme import Theme
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "rich", "--quiet"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
    from rich.text import Text
    from rich.theme import Theme

# ─── Aesthetic Configuration ────────────────────────────────────────────────
custom_theme = Theme({
    "info": "cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "phase": "bold magenta",
    "hacker": "bold green",
    "dim": "grey50",
})

console = Console(theme=custom_theme)

BANNER = r"""
    _____           ___                    __
   / ___/___  _____/   | ____ ____  ____  / /______
   \__ \/ _ \/ ___/ /| |/ __ `/ _ \/ __ \/ __/ ___/
  ___/ /  __/ /__/ ___ / /_/ /  __/ / / / /_(__  )
 /____/\___/\___/_/  |_\__, /\___/_/ /_/_/   \___/
                      /____/
"""

def run_git(cmd: str, cwd: Path):
    return subprocess.run(cmd, cwd=str(cwd), shell=True, text=True, capture_output=True)

def main():
    console.print(Text(BANNER, style="hacker"), justify="center")
    console.print(Panel(Text("FRAMEWORK SYNCHRONIZATION & INTELLIGENCE RECALL", justify="center", style="bold white"), border_style="hacker"))
    
    root = Path(__file__).parent.resolve()
    
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        
        # 1. Validation
        task = progress.add_task("Verifying uplink integrity...", total=None)
        if not shutil.which("git"):
            console.print("[error]󰅚 Uplink failed: Git binary not detected.[/error]")
            sys.exit(1)
        
        # 2. Connection
        progress.update(task, description="Establishing secure connection to origin...")
        fetch = run_git("git fetch origin", root)
        if fetch.returncode != 0:
            console.print(f"[error]󰅚 Synchronization failed: {fetch.stderr.strip()}[/error]")
            sys.exit(1)
            
        # 3. Analysis
        progress.update(task, description="Analyzing local vs remote intelligence delta...")
        local_rev = run_git("git rev-parse HEAD", root).stdout.strip()
        try:
            remote_rev = run_git("git rev-parse @{u}", root).stdout.strip()
        except:
            console.print("[error]󰅚 Intelligence recall failed: Could not resolve upstream.[/error]")
            sys.exit(1)
            
        if local_rev == remote_rev:
            console.print(f"\n[success]󰄬 Framework is fully synchronized (Rev: {local_rev[:7]})[/success]")
            try:
                console.print("\n")
                choice = console.input("[bold magenta]::[/bold magenta] Re-run deployment sequence to verify arsenal? [y/N]: ").lower()
            except: return
            if choice != 'y': return
        else:
            console.print(f"\n[warning]󱈸 New intelligence detected. Synchronizing delta...[/warning]")
            pull = run_git("git pull", root)
            if pull.returncode != 0:
                console.print("[error]󰅚 Synchronization collapsed. Conflict detected.[/error]")
                console.print(f"\n  [dim]{pull.stderr.strip()}[/dim]\n")
                
                # Robust conflict handling
                try:
                    console.print("[bold yellow]RECOVERY OPTION:[/bold yellow]")
                    console.print("Local changes detected in core files. Favoring framework integrity is recommended.")
                    confirm = console.input("  [bold magenta]::[/bold magenta] Overwrite local changes and force synchronize? [y/N]: ").lower()
                    if confirm == 'y':
                        console.print("[info]󰋼 Forcing synchronization via hard reset...[/info]")
                        reset = run_git("git reset --hard origin/main", root)
                        if reset.returncode == 0:
                            console.print("[success]󰄬 Framework integrity restored.[/success]")
                        else:
                            console.print(f"[error]󰅚 Recovery failed: {reset.stderr.strip()}[/error]")
                            sys.exit(1)
                    else:
                        console.print("[error]󰅚 Update aborted by user.[/error]")
                        sys.exit(1)
                except (KeyboardInterrupt, EOFError):
                    sys.exit(1)
            else:
                console.print("[success]󰄬 New intelligence integrated successfully.[/success]")

    # 4. Handover
    console.print("\n[info]󰋼 Initiating deployment sequence to arm modules...[/info]\n")
    try:
        subprocess.run([sys.executable, "installer.py"] + sys.argv[1:], cwd=str(root))
    except Exception as e:
        console.print(f"[error]󰅚 Deployment sequence failed: {e}[/error]")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[error]Aborted.[/error]")
        sys.exit(130)
