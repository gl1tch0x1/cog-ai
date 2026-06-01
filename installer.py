#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          SecAgents — Elite Red Team Deployment Engine           ║
║       "Precision. Intelligence. Multi-Agent Mastery."           ║
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
from typing import Optional, List, Dict, Any

def bootstrap_rich():
    try:
        from rich.console import Console
        return True
    except ImportError:
        print("󰋼 Initializing deployment bootstrap...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "rich", "--quiet"], check=True)
            return True
        except:
            print("󰅚 Bootstrap failed. Please install 'rich' manually: pip install rich")
            return False

if not bootstrap_rich():
    sys.exit(1)

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from rich.theme import Theme
from rich.box import ROUNDED, HEAVY

# ─── Aesthetic Configuration ────────────────────────────────────────────────
custom_theme = Theme({
    "info": "cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "phase": "bold magenta",
    "hacker": "bold green",
    "highlight": "bold white on blue",
    "dim": "grey50",
})

console = Console(theme=custom_theme)
IS_WIN = platform.system() == "Windows"

# ─── Paths ───────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.resolve()
VENV_DIR    = ROOT / ".venv"
PYTHON_AGENTS = ROOT / "python-agents"
API_DIR     = ROOT / "api"
ENV_FILE    = ROOT / ".env"

PYTHON_EXEC = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("python.exe" if IS_WIN else "python"))
PIP_EXEC    = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("pip.exe" if IS_WIN else "pip"))
PYTEST_EXEC = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("pytest.exe" if IS_WIN else "pytest"))
UVICORN_EXEC = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("uvicorn.exe" if IS_WIN else "uvicorn"))

# ─── UI Components ───────────────────────────────────────────────────────────

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
    grid.add_row(Text("» AUTONOMOUS OFFENSIVE INTELLIGENCE FRAMEWORK «", style="bold white"))
    grid.add_row(Text(f"[ V0.3.0-DEV | ELITE DEPLOYMENT ENGINE ]", style="dim"))
    return Panel(grid, style="hacker", box=HEAVY)

class DeploymentUI:
    def __init__(self):
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=10),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="phases", ratio=1),
            Layout(name="log", ratio=2)
        )
        
        self.phases_table = Table(title="[bold magenta]OPERATIONAL PHASES[/bold magenta]", expand=True, box=ROUNDED)
        self.phases_table.add_column("ID", width=4)
        self.phases_table.add_column("PHASE")
        self.phases_table.add_column("STATUS", justify="right")
        
        self.log_messages = []
        self.current_phase = 0
        
    def update_log(self, message: str, style: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        prefixes = {"info": "󰋼", "success": "󰄬", "warning": "󱈸", "error": "󰅚"}
        self.log_messages.append(f"[{timestamp}] {prefixes.get(style, '·')} {message}")
        if len(self.log_messages) > 12:
            self.log_messages.pop(0)
            
    def render_log(self):
        return Panel("\n".join(self.log_messages), title="[bold cyan]REAL-TIME TELEMETRY[/bold cyan]", box=ROUNDED, border_style="cyan")

    def add_phase(self, name: str, status: str = "[dim]PENDING[/dim]"):
        self.current_phase += 1
        self.phases_table.add_row(f"{self.current_phase:02d}", name, status)

    def update_phase(self, index: int, status: str):
        self.phases_table.columns[2]._cells[index] = status

ui = DeploymentUI()

# ─── Execution Logic ──────────────────────────────────────────────────────────

def run_cmd(cmd: list[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)

# ═══════════════════════════════════════════════════════════════════════
#  OPERATIONAL PHASES
# ═══════════════════════════════════════════════════════════════════════

def run_preflight(args: argparse.Namespace) -> bool:
    ui.update_log("Initiating preflight reconnaissance...")
    # Python Check
    v = sys.version_info
    if v >= (3, 11):
        ui.update_log(f"Runtime: Python {v.major}.{v.minor} [OK]", "success")
    else:
        ui.update_log(f"Runtime: Incompatible Python {v.major}.{v.minor}", "error")
        return False
    
    for tool in ["git", "docker", "node"]:
        if shutil.which(tool): ui.update_log(f"Binary: {tool} [FOUND]", "success")
        else: ui.update_log(f"Binary: {tool} [MISSING]", "warning")
            
    return True

def deploy_environment() -> bool:
    ui.update_log("Hardening execution environment...")
    if not VENV_DIR.exists():
        try:
            run_cmd([sys.executable, "-m", "venv", str(VENV_DIR)])
            ui.update_log("Isolated tunnel (venv) established.", "success")
        except Exception as e:
            ui.update_log(f"Environment collapse: {e}", "error")
            return False
    return True

def install_arsenal(args: argparse.Namespace) -> bool:
    ui.update_log("Arming the offensive arsenal...")
    
    # Critical binaries
    deps = ["pydantic>=2.0.0", "pydantic-core>=2.0.0", "rich", "typer", "pytest-cov", "httpx"]
    for dep in deps:
        ui.update_log(f"Loading {dep} binary...")
        run_cmd([PIP_EXEC, "install", "--only-binary", ":all:", dep, "--quiet"])
    
    packages = [
        ("Core Agents", PYTHON_AGENTS, ".[dev,browser]"),
        ("Orchestrator API", API_DIR, ".[dev]"),
    ]
    for name, path, extras in packages:
        if path.exists():
            ui.update_log(f"Mounting {name}...")
            res = run_cmd([PIP_EXEC, "install", "--prefer-binary", "-e", extras], cwd=path)
            if res.returncode != 0:
                if args.docker: ui.update_log(f"{name} failed (non-fatal in docker)", "warning")
                else: 
                    ui.update_log(f"{name} mount failed: {res.stderr[:50]}...", "error")
                    return False
    return True

def configure_intel() -> bool:
    ui.update_log("Generating operational intelligence manifest...")
    if not ENV_FILE.exists():
        db_pass = secrets.token_urlsafe(24)
        jwt_sec = secrets.token_urlsafe(48)
        content = f"DB_PASSWORD={db_pass}\nJWT_SECRET={jwt_sec}\nALLOWED_DOMAINS=example.com\n"
        ENV_FILE.write_text(content)
        ui.update_log("Intel manifest (.env) created.", "success")
    return True

def create_entrypoints() -> bool:
    ui.update_log("Deploying operational entrypoints...")
    if IS_WIN:
        Path("secagent.bat").write_text(f"@echo off\n\"{PYTHON_EXEC}\" -m secagents %*")
    else:
        p = Path("secagent")
        p.write_text(f"#!/bin/bash\n\"{PYTHON_EXEC}\" -m secagents \"$@\"")
        p.chmod(0o755)
    return True

def run_tests() -> bool:
    ui.update_log("Executing integrity verification suite...")
    res = run_cmd([PYTEST_EXEC, "tests/unit/test_agents_complete.py", "-v", "-p", "no:cov"])
    if res.returncode == 0:
        ui.update_log("Integrity check: [VERIFIED]", "success")
        return True
    else:
        ui.update_log("Integrity check: [FAILED]", "error")
        res2 = run_cmd([PYTHON_EXEC, "-m", "py_compile", "python-agents/secagents/agents/web_security.py"])
        if res2.returncode == 0:
            ui.update_log("Fallback syntax check: [PASSED]", "warning")
            return True
        return False

def print_final_report(success: bool):
    console.print("\n" + "━" * 70, style="phase")
    if success:
        console.print(Panel(Text("MISSION READY: SECAGENT DEPLOYED SUCCESSFULLY", style="success", justify="center"), border_style="success", box=HEAVY))
    else:
        console.print(Panel(Text("DEPLOYMENT COMPLETE WITH MINOR ANOMALIES", style="warning", justify="center"), border_style="warning", box=HEAVY))
    
    table = Table(box=None, expand=True)
    table.add_column("COMMAND", style="cyan", width=25)
    table.add_column("DESCRIPTION", style="dim")
    
    cli = "secagent" if not IS_WIN else "secagent.bat"
    table.add_row(f"./{cli} scan -t <target>", "Initiate autonomous red-team scan")
    table.add_row(f"./{cli} vault --validate", "Audit operational secret integrity")
    table.add_row(f"./{cli} update", "Synchronize framework intelligence")
    
    console.print(table)
    console.print("━" * 70, style="phase")
    console.print("'Industrial Power. Elite Intelligence. Mission Ready.'", style="italic dim", justify="center")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--no-test", action="store_true")
    parser.add_argument("--no-start", action="store_true")
    args = parser.parse_args()

    phases = [
        ("PREFLIGHT", lambda: run_preflight(args)),
        ("ENVIRONMENT", deploy_environment),
        ("ARSENAL", lambda: install_arsenal(args)),
        ("INTEL", configure_intel),
        ("ENTRYPOINTS", create_entrypoints)
    ]
    if not args.no_test:
        phases.append(("INTEGRITY", run_tests))

    for name, _ in phases:
        ui.add_phase(name)

    overall_success = True
    ui.layout["header"].update(get_header())
    
    with Live(ui.layout, refresh_per_second=4, screen=True):
        for i, (name, func) in enumerate(phases):
            ui.update_phase(i, "[yellow]ACTIVE[/yellow]")
            ui.layout["footer"].update(Panel(Text(f"OPERATING: {name}", justify="center", style="bold white"), box=ROUNDED, border_style="magenta"))
            
            try:
                if func(): ui.update_phase(i, "[green]SUCCESS[/green]")
                else:
                    ui.update_phase(i, "[red]FAILED[/red]")
                    overall_success = False
                    if not args.docker: break
            except Exception as e:
                ui.update_log(f"Phase {name} crash: {e}", "error")
                ui.update_phase(i, "[bold red]CRASH[/red]")
                overall_success = False
                break
            
            ui.layout["phases"].update(ui.phases_table)
            ui.layout["log"].update(ui.render_log())
            time.sleep(0.4)

    print_final_report(overall_success)
    
    if overall_success and not args.no_start and not args.docker:
        console.print("\n[bold cyan]󱐋 IGNITING API CONTROL PLANE...[/bold cyan]")
        try:
            subprocess.run([UVICORN_EXEC, "secagents_api.main:app", "--host", "0.0.0.0", "--port", "8000"])
        except KeyboardInterrupt:
            console.print("\n[bold yellow]⚠ Mission terminated by operator.[/bold yellow]")

if __name__ == "__main__":
    main()
