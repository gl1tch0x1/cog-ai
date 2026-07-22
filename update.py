#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          SecAgents — Intelligence Recall Utility                 ║
║       "Synchronizing the Arsenal. Redefining the Edge."         ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import subprocess
import sys
import shutil
import time
from pathlib import Path

def bootstrap_rich():
    try:
        from rich.console import Console
        return True
    except ImportError:
        print("󰋼 Initializing intelligence recall bootstrap...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "rich", "--quiet"], check=True)
            return True
        except:
            print("󰅚 Bootstrap failed. Please install 'rich' manually.")
            return False

if not bootstrap_rich():
    sys.exit(1)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.theme import Theme
from rich.layout import Layout
from rich.box import ROUNDED, HEAVY

# ─── Aesthetic Configuration ────────────────────────────────────────────────
custom_theme = Theme({
    "info": "bold #00ffff",
    "warning": "bold #ffaa00",
    "error": "bold #ff003c",
    "success": "bold #00ff00",
    "phase": "bold #ff00ff",
    "hacker": "bold #00ff00",
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


def get_header():
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_row(Text(BANNER, style="hacker"))
    grid.add_row(Text.from_markup("[bold white]» FRAMEWORK SYNCHRONIZATION & INTELLIGENCE RECALL «[/]"))
    return Panel(grid, border_style="#00ff00", box=HEAVY, padding=(1, 2))

class UpdateUI:
    def __init__(self):
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=10),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.log_messages = []
        
    def update_log(self, message: str, style: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        prefixes = {"info": "󰋼", "success": "󰄬", "warning": "󱈸", "error": "󰅚"}
        self.log_messages.append(f"[{timestamp}] {prefixes.get(style, '·')} {message}")
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
            
    def render_main(self):
        return Panel("\n".join(self.log_messages), title="[bold cyan]SYNCHRONIZATION TELEMETRY[/bold cyan]", box=ROUNDED, border_style="cyan")

ui = UpdateUI()

def run_git(cmd: str, cwd: Path):
    return subprocess.run(cmd, cwd=str(cwd), shell=True, text=True, capture_output=True)

def main():
    root = Path(__file__).parent.resolve()
    ui.layout["header"].update(get_header())
    ui.layout["footer"].update(Panel(Text("ESTABLISHING UPLINK...", justify="center", style="bold white"), box=ROUNDED, border_style="dim"))

    with Live(ui.layout, console=console, refresh_per_second=4, screen=True):
        # 1. Validation
        ui.update_log("Verifying Git uplink integrity...")
        if not shutil.which("git"):
            ui.update_log("Git binary not detected. Uplink failed.", "error")
            time.sleep(2)
            return
        
        # 2. Connection
        ui.update_log("Establishing secure connection to origin...")
        fetch = run_git("git fetch origin", root)
        if fetch.returncode != 0:
            ui.update_log(f"Synchronization failed: {fetch.stderr.strip()[:50]}...", "error")
            time.sleep(2)
            return
            
        # 3. Delta Analysis
        ui.update_log("Analyzing intelligence delta...")
        local_rev = run_git("git rev-parse HEAD", root).stdout.strip()
        try:
            remote_rev = run_git("git rev-parse @{u}", root).stdout.strip()
        except Exception:
            ui.update_log("Could not resolve upstream branch.", "error")
            time.sleep(2)
            return
            
        ui.layout["main"].update(ui.render_main())

        if local_rev == remote_rev:
            ui.update_log(f"Framework is fully synchronized (Rev: {local_rev[:7]})", "success")
            ui.layout["footer"].update(Panel(Text("OPERATIONAL READINESS VERIFIED", justify="center", style="success"), box=ROUNDED, border_style="success"))
            time.sleep(1)
            # Continue to installer to ensure dependencies
        else:
            ui.update_log("New intelligence detected. Synchronizing...", "warning")
            pull = run_git("git pull", root)
            
            if pull.returncode != 0:
                ui.update_log("Synchronization collapsed. Conflict detected.", "error")
                ui.layout["main"].update(ui.render_main())
                time.sleep(1)
                
                # Recovery
                ui.layout["footer"].update(Panel(Text("CONFLICT DETECTED — RECOVERY REQUIRED", justify="center", style="bold red"), box=ROUNDED, border_style="red"))
                
                # We need to exit Live to get user input safely
                # But we can try to get it inside if we're careful
                pass 
            else:
                ui.update_log("Intelligence integrated successfully.", "success")
                ui.layout["footer"].update(Panel(Text("INTELLIGENCE RECALL COMPLETE", justify="center", style="success"), box=ROUNDED, border_style="success"))
                time.sleep(1)

    # Post-Live recovery and handover
    # Check if we need to force reset
    local_rev = run_git("git rev-parse HEAD", root).stdout.strip()
    remote_rev = run_git("git rev-parse @{u}", root).stdout.strip()
    
    if local_rev != remote_rev:
        console.print("\n[bold yellow]󱈸 RECOVERY OPTION:[/bold yellow]")
        console.print("Local changes detected in core files. Favoring framework integrity is recommended.")
        try:
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

    # 4. Handover to Installer
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
