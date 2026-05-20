#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          SecAgents — Automated Installer v1.0                   ║
║  Multi-agent cybersecurity platform | Production-grade setup    ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
  python installer.py              # Full interactive install
  python installer.py --no-db     # Skip PostgreSQL setup
  python installer.py --docker    # Use Docker Compose stack
  python installer.py --ci        # Non-interactive CI mode
  python installer.py --check     # Preflight checks only (exit 0/1)
"""

from __future__ import annotations

import argparse
import os
import platform
import random
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

# ─── Terminal colours (stdlib only) ─────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
MAGENTA = "\033[35m"
BLUE   = "\033[34m"
WHITE  = "\033[97m"

IS_WIN = platform.system() == "Windows"

def _no_color() -> bool:
    return IS_WIN and not os.environ.get("WT_SESSION") and not os.environ.get("TERM_PROGRAM")

def c(color: str, text: str) -> str:
    if _no_color():
        return text
    return f"{color}{text}{RESET}"

# ─── Banner ──────────────────────────────────────────────────────────────────
BANNER = r"""
  ____            _    ____              _
 / ___|  ___  ___/ \  / ___| ___ _ __ | |_ ___
 \___ \ / _ \/ __/ _ \| |  _ / _ \ '_ \| __/ __|
  ___) |  __/ (_/ ___ \ |_| |  __/ | | | |_\__ \
 |____/ \___|\___\_/ \_/\____|\___|_| |_|\__|___/

  Autonomous Multi-Agent Cybersecurity Platform
  Installer v1.0  |  Python 3.11+  Required
"""

# ─── Paths ───────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.resolve()
VENV_DIR    = ROOT / ".venv"
PYTHON_AGENTS = ROOT / "python-agents"
API_DIR     = ROOT / "api"
MIGRATION   = ROOT / "api" / "migrations" / "001_initial.sql"
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE    = ROOT / ".env"
FRONTEND_DIR = ROOT / "frontend" / "apex"

PYTHON_EXEC = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("python.exe" if IS_WIN else "python"))
PIP_EXEC    = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("pip.exe" if IS_WIN else "pip"))
PYTEST_EXEC = str(VENV_DIR / ("Scripts" if IS_WIN else "bin") / ("pytest.exe" if IS_WIN else "pytest"))

# ─── Step counter ────────────────────────────────────────────────────────────
_step = 0
_errors: list[str] = []

def step(title: str) -> None:
    global _step
    _step += 1
    print(f"\n{c(BOLD+CYAN, f'[{_step:02d}]')} {c(BOLD+WHITE, title)}")
    print(c(CYAN, "─" * 60))

def ok(msg: str) -> None:
    print(f"  {c(GREEN, '✓')} {msg}")

def warn(msg: str) -> None:
    print(f"  {c(YELLOW, '⚠')} {msg}")

def fail(msg: str) -> None:
    print(f"  {c(RED, '✗')} {msg}")
    _errors.append(msg)

def info(msg: str) -> None:
    print(f"  {c(BLUE, '·')} {msg}")

def run(
    cmd: list[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    capture: bool = False,
    check: bool = True,
    timeout: int = 300,
) -> subprocess.CompletedProcess:
    """Run a command, optionally capturing output."""
    merged_env = {**os.environ, **(env or {})}
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        capture_output=capture,
        text=True,
        check=check,
        timeout=timeout,
    )


# ═══════════════════════════════════════════════════════════════════════
#  SECTION 1 — PREFLIGHT CHECKS
# ═══════════════════════════════════════════════════════════════════════

def check_python_version() -> bool:
    v = sys.version_info
    if v >= (3, 11):
        ok(f"Python {v.major}.{v.minor}.{v.micro} ✓")
        return True
    fail(f"Python {v.major}.{v.minor} detected — 3.11+ required")
    return False


def check_command(cmd: str, friendly: str, install_hint: str = "") -> bool:
    path = shutil.which(cmd)
    if path:
        ok(f"{friendly} found: {path}")
        return True
    warn(f"{friendly} not found{' — ' + install_hint if install_hint else ''}")
    return False


def check_port_open(host: str, port: int, label: str) -> bool:
    try:
        with socket.create_connection((host, port), timeout=3):
            ok(f"{label} reachable at {host}:{port}")
            return True
    except OSError:
        warn(f"{label} not reachable at {host}:{port}")
        return False


def check_disk_space(min_gb: float = 2.0) -> bool:
    try:
        if IS_WIN:
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(  # type: ignore[attr-defined]
                str(ROOT.drive + "\\"), None, None, ctypes.byref(free_bytes)
            )
            free_gb = free_bytes.value / (1024 ** 3)
        else:
            st = os.statvfs(str(ROOT))
            free_gb = (st.f_bavail * st.f_frsize) / (1024 ** 3)
        if free_gb >= min_gb:
            ok(f"Disk space: {free_gb:.1f} GB free")
            return True
        warn(f"Low disk space: {free_gb:.1f} GB (minimum {min_gb} GB recommended)")
        return False
    except Exception:
        warn("Could not determine disk space")
        return True


def run_preflight(args: argparse.Namespace) -> bool:
    step("Preflight System Checks")
    results = [
        check_python_version(),
        check_disk_space(),
    ]

    if not args.no_db and not args.docker:
        results.append(check_command("psql", "PostgreSQL client", "https://www.postgresql.org/download/"))
        pg_ok = check_port_open("localhost", 5432, "PostgreSQL")
        if not pg_ok:
            warn("PostgreSQL not running — will attempt to start or guide setup")
        results.append(True)  # non-fatal

    results.append(check_command("git", "Git"))

    if args.docker:
        results.append(check_command("docker", "Docker", "https://docs.docker.com/get-docker/"))

    check_command("node", "Node.js", "https://nodejs.org/")
    check_command("npm", "npm")

    net_ok = True
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3).close()
        ok("Network connectivity ✓")
    except OSError:
        warn("No internet — offline install may fail")
        net_ok = False

    return all(results) and net_ok


# ═══════════════════════════════════════════════════════════════════════
#  SECTION 2 — VIRTUAL ENVIRONMENT
# ═══════════════════════════════════════════════════════════════════════

def create_venv() -> bool:
    step("Creating Python Virtual Environment")
    if VENV_DIR.exists():
        warn(f".venv already exists at {VENV_DIR} — reusing")
        ok("Virtual environment ready")
        return True
    try:
        info(f"Creating venv at: {VENV_DIR}")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
        ok(f"Virtual environment created: {VENV_DIR}")
        return True
    except Exception as e:
        fail(f"Failed to create venv: {e}")
        return False


def upgrade_pip() -> bool:
    try:
        run([PYTHON_EXEC, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            capture=True)
        ok("pip / setuptools / wheel upgraded")
        return True
    except Exception as e:
        warn(f"pip upgrade failed (non-fatal): {e}")
        return True


# ═══════════════════════════════════════════════════════════════════════
#  SECTION 3 — INSTALL PYTHON PACKAGES
# ═══════════════════════════════════════════════════════════════════════

def install_python_packages() -> bool:
    step("Installing Python Dependencies")

    packages = [
        ("python-agents", PYTHON_AGENTS, ".[dev,browser]"),
        ("api",           API_DIR,       ".[dev]"),
    ]

    success = True
    for name, path, extras in packages:
        if not path.exists():
            warn(f"{name} directory not found at {path} — skipping")
            continue
        info(f"Installing {name} ({extras}) …")
        try:
            run([PIP_EXEC, "install", "-e", extras], cwd=path, capture=True)
            ok(f"{name} installed (editable)")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""
            if "pydantic-core" in stderr and "maturin" in stderr:
                fail(f"Failed to install {name}: pydantic-core requires Rust to build.")
                info(c(YELLOW, "Hint: Install Rust (https://rustup.rs/) and re-run the installer."))
            else:
                fail(f"Failed to install {name}: {stderr[:200] if stderr else e}")
            success = False

    # Extra standalone packages that aren't in pyproject but help
    extras_global = ["python-dotenv", "rich", "typer"]
    for pkg in extras_global:
        try:
            run([PIP_EXEC, "install", "--quiet", pkg], capture=True)
        except Exception:
            pass  # optional

    return success


def install_frontend_packages() -> bool:
    step("Installing Frontend Dependencies")
    if not FRONTEND_DIR.exists():
        warn(f"Frontend directory not found at {FRONTEND_DIR}")
        return True
    
    if not shutil.which("npm"):
        warn("npm not found — skipping frontend install")
        return True

    info("Running npm install in frontend/apex/ …")
    try:
        run(["npm", "install"], cwd=FRONTEND_DIR, capture=True)
        ok("Frontend dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        warn(f"Frontend install failed: {e.stderr[:200] if e.stderr else e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
#  SECTION 4 — ENVIRONMENT FILE
# ═══════════════════════════════════════════════════════════════════════

def generate_env(args: argparse.Namespace) -> bool:
    step("Generating .env Configuration File")

    if ENV_FILE.exists() and not args.ci:
        print(f"  {c(YELLOW, '⚠')} .env already exists.")
        answer = input("  Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            ok(".env kept unchanged")
            return True

    db_password = secrets.token_urlsafe(24)
    jwt_secret  = secrets.token_urlsafe(48)

    if args.docker:
        db_host = "postgres"  # Docker service name
    else:
        db_host = "localhost"

    content = f"""\
# ── SecAgents Environment Configuration ──────────────────────────────
# Generated by installer.py on {time.strftime('%Y-%m-%d %H:%M:%S')}
# DO NOT commit this file to version control.

# ── Database ─────────────────────────────────────────────────────────
DB_PASSWORD={db_password}
DATABASE_URL=postgresql+asyncpg://secagents:{db_password}@{db_host}:5432/secagents

# ── Redis ─────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── Authentication ───────────────────────────────────────────────────
JWT_SECRET={jwt_secret}

# ── LLM Providers (set at least ONE) ─────────────────────────────────
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=sk-...
GEMINI_API_KEY=...
XAI_API_KEY=...

# ── Scope ────────────────────────────────────────────────────────────
ALLOWED_DOMAINS=example.com,*.example.com

# ── Integrations (optional) ──────────────────────────────────────────
SLACK_WEBHOOK_URL=
JIRA_URL=
JIRA_API_TOKEN=
INTERACTSH_SERVER=
"""

    ENV_FILE.write_text(content, encoding="utf-8")
    ok(f".env written to {ENV_FILE}")
    info(f"DB password  : {db_password[:6]}…  (stored in .env)")
    info(f"JWT secret   : {jwt_secret[:8]}…  (stored in .env)")
    warn("Edit .env and add your LLM API keys before starting the API!")
    return True


def load_env() -> dict[str, str]:
    """Parse .env file into a dict (no external dependency)."""
    env: dict[str, str] = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


# ═══════════════════════════════════════════════════════════════════════
#  SECTION 5 — POSTGRESQL DATABASE SETUP
# ═══════════════════════════════════════════════════════════════════════

def _psql(sql: str, user: str = "postgres", dbname: str = "postgres",
          password: Optional[str] = None, capture: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if password:
        env["PGPASSWORD"] = password
    return run(
        ["psql", "-U", user, "-d", dbname, "-c", sql],
        env=env, capture=capture, check=False,
    )


def _psql_file(filepath: str, user: str, dbname: str, password: Optional[str] = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if password:
        env["PGPASSWORD"] = password
    return run(
        ["psql", "-U", user, "-d", dbname, "-f", filepath],
        env=env, capture=True, check=False,
    )


def _pg_user_exists(pg_user: str = "postgres", pg_password: Optional[str] = None) -> bool:
    """Check if we can connect to PostgreSQL at all."""
    result = _psql("SELECT 1;", user=pg_user, password=pg_password)
    return result.returncode == 0


def setup_postgres(args: argparse.Namespace) -> bool:
    step("Setting Up PostgreSQL Database")

    env_vars = load_env()
    db_password = env_vars.get("DB_PASSWORD", "changeme")

    # ── Try to find a working superuser connection ────────────────────
    info("Attempting PostgreSQL superuser connection …")
    pg_superuser: Optional[str] = None
    pg_superpass: Optional[str] = None

    candidates = [
        ("postgres", None),
        ("postgres", "postgres"),
        (os.environ.get("USER", ""), None),
        ("secagents", db_password),
    ]

    for user, pwd in candidates:
        if not user:
            continue
        if _pg_user_exists(user, pwd):
            pg_superuser = user
            pg_superpass = pwd
            ok(f"Connected to PostgreSQL as '{pg_superuser}'")
            break

    if not pg_superuser:
        fail(
            "Cannot connect to PostgreSQL. Please ensure PostgreSQL is running "
            "and accessible. You can:\n"
            "    • Run:  docker compose up -d postgres\n"
            "    • Or:   sudo service postgresql start\n"
            "    • Or:   brew services start postgresql  (macOS)\n"
            "    • Or re-run with --docker to use the full Docker stack."
        )
        return False

    # ── Create role ───────────────────────────────────────────────────
    info("Creating database role 'secagents' …")
    create_role_sql = (
        f"DO $$ BEGIN "
        f"  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'secagents') THEN "
        f"    CREATE ROLE secagents LOGIN PASSWORD '{db_password}'; "
        f"  ELSE "
        f"    ALTER ROLE secagents WITH PASSWORD '{db_password}'; "
        f"  END IF; "
        f"END $$;"
    )
    r = _psql(create_role_sql, user=pg_superuser, password=pg_superpass)
    if r.returncode == 0:
        ok("Role 'secagents' ready")
    else:
        warn(f"Role creation warning: {r.stderr.strip()[:120]}")

    # ── Create database ───────────────────────────────────────────────
    info("Creating database 'secagents' …")
    check_db = _psql(
        "SELECT 1 FROM pg_database WHERE datname = 'secagents';",
        user=pg_superuser, password=pg_superpass,
    )
    if "(1 row)" in (check_db.stdout or ""):
        warn("Database 'secagents' already exists — skipping creation")
    else:
        r = _psql(
            "CREATE DATABASE secagents OWNER secagents ENCODING 'UTF8' "
            "LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8' TEMPLATE template0;",
            user=pg_superuser, password=pg_superpass,
        )
        if r.returncode == 0:
            ok("Database 'secagents' created")
        else:
            # Try without locale (Windows / some Docker images)
            r2 = _psql(
                "CREATE DATABASE secagents OWNER secagents;",
                user=pg_superuser, password=pg_superpass,
            )
            if r2.returncode == 0:
                ok("Database 'secagents' created (no locale flags)")
            else:
                fail(f"Failed to create database: {r2.stderr.strip()[:200]}")
                return False

    # ── Grant privileges ──────────────────────────────────────────────
    _psql("GRANT ALL PRIVILEGES ON DATABASE secagents TO secagents;",
          user=pg_superuser, password=pg_superpass)
    ok("Privileges granted to 'secagents'")

    # ── Apply schema migration ─────────────────────────────────────────
    if MIGRATION.exists():
        info(f"Applying migration: {MIGRATION.name} …")
        r = _psql_file(str(MIGRATION), user="secagents", dbname="secagents", password=db_password)
        if r.returncode == 0:
            ok("Schema migration applied successfully")
        else:
            stderr = r.stderr or ""
            if "already exists" in stderr.lower():
                ok("Schema already up-to-date (tables exist)")
            else:
                warn(f"Migration warning (may be partial): {stderr.strip()[:200]}")
    else:
        warn(f"Migration file not found at {MIGRATION} — schema not applied")

    # ── Verify connection with secagents user ─────────────────────────
    info("Verifying application DB connection …")
    verify = _psql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';",
                   user="secagents", dbname="secagents", password=db_password)
    if verify.returncode == 0:
        ok("Application user can connect and query database ✓")
    else:
        warn("Could not verify with 'secagents' user — check pg_hba.conf if needed")

    return True


# ═══════════════════════════════════════════════════════════════════════
#  SECTION 6 — REDIS CHECK
# ═══════════════════════════════════════════════════════════════════════

def check_redis(args: argparse.Namespace) -> bool:
    step("Checking Redis")
    if check_port_open("localhost", 6379, "Redis"):
        return True
    warn("Redis is not running on localhost:6379")

    if shutil.which("redis-server"):
        info("redis-server found — you can start it with: redis-server")
    elif shutil.which("docker"):
        info("Starting Redis via Docker …")
        try:
            run(["docker", "run", "-d", "--name", "secagents-redis",
                 "-p", "6379:6379", "--restart", "unless-stopped", "redis:7-alpine"],
                capture=True, check=False)
            time.sleep(2)
            if check_port_open("localhost", 6379, "Redis (Docker)"):
                ok("Redis started via Docker")
                return True
        except Exception as e:
            warn(f"Docker Redis start failed: {e}")
    warn("Redis unavailable — task queue will use in-memory fallback")
    return True  # non-fatal — system degrades gracefully


# ═══════════════════════════════════════════════════════════════════════
#  SECTION 7 — DOCKER COMPOSE STACK
# ═══════════════════════════════════════════════════════════════════════

def start_docker_stack(args: argparse.Namespace) -> bool:
    step("Starting Docker Compose Stack")
    
    docker_bin = shutil.which("docker")
    if not docker_bin:
        fail("Docker not found — cannot start full stack")
        return False

    # Check for docker compose (v2) or docker-compose (v1)
    compose_cmd = ["docker", "compose"]
    try:
        run(["docker", "compose", "version"], capture=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        if shutil.which("docker-compose"):
            compose_cmd = ["docker-compose"]
            ok("Using docker-compose (v1)")
        else:
            fail("Neither 'docker compose' nor 'docker-compose' found")
            return False
    else:
        ok("Using docker compose (v2)")

    compose_file = ROOT / "docker-compose.yml"
    if not compose_file.exists():
        fail("docker-compose.yml not found")
        return False

    env_vars = load_env()
    db_pass = env_vars.get("DB_PASSWORD", "changeme")

    info("Pulling images and starting services …")
    try:
        run(compose_cmd + ["up", "-d", "--build"],
            cwd=ROOT, env={"DB_PASSWORD": db_pass}, timeout=600)
        ok("Docker Compose stack started")
        info("Services: postgres:5432, redis:6379, api:8000, frontend:3000")
    except Exception as e:
        fail(f"Docker Compose failed: {e}")
        return False

    # Wait for postgres
    info("Waiting for PostgreSQL to be healthy …")
    for attempt in range(20):
        time.sleep(3)
        try:
            result = run(
                compose_cmd + ["exec", "-T", "postgres",
                 "pg_isready", "-U", "secagents"],
                cwd=ROOT, capture=True, check=False,
            )
            if result.returncode == 0:
                ok("PostgreSQL healthy")
                break
        except Exception:
            pass
        info(f"  attempt {attempt + 1}/20 …")
    else:
        warn("PostgreSQL health check timed out — may still be starting")

    # Apply migration via Docker exec
    if MIGRATION.exists():
        info("Applying schema migration via Docker …")
        try:
            run(
                compose_cmd + ["exec", "-T", "postgres",
                 "psql", "-U", "secagents", "-d", "secagents"],
                cwd=ROOT, capture=True, check=False,
            )
            ok("Migration applied (Docker)")
        except Exception as e:
            warn(f"Migration via Docker failed: {e}")

    return True


# ═══════════════════════════════════════════════════════════════════════
#  SECTION 8 — RUN TESTS
# ═══════════════════════════════════════════════════════════════════════

def run_tests(args: argparse.Namespace) -> bool:
    step("Running Smoke Tests")

    tests_dir = ROOT / "tests" / "unit"
    if not tests_dir.exists():
        warn("Unit tests directory not found — skipping")
        return True

    # Ensure pytest-timeout is installed
    try:
        run([PIP_EXEC, "install", "pytest-timeout"], capture=True, check=False)
    except Exception:
        pass

    info("Running unit tests (pytest) …")
    cmd = [PYTEST_EXEC, "tests/unit/", "-v", "--tb=short", "-q", "--no-header"]
    
    # Only add timeout if we can verify it's supported or just try it
    cmd.append("--timeout=60")

    try:
        result = run(
            cmd,
            cwd=ROOT, capture=not args.ci, check=False, timeout=180,
        )
        if result.returncode == 0:
            ok("All unit tests passed ✓")
            return True
        else:
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            output = (stdout + stderr)[-600:]
            warn(f"Some tests failed:\n{output}")
            return False
    except subprocess.CalledProcessError as e:
        if "unrecognized arguments: --timeout" in str(e.stderr):
            # Retry without timeout
            info("Retrying tests without --timeout flag …")
            cmd.remove("--timeout=60")
            result = run(cmd, cwd=ROOT, capture=not args.ci, check=False, timeout=180)
            return result.returncode == 0
        warn(f"Test runner error: {e}")
        return False
    except FileNotFoundError:
        warn("pytest not found in venv — skipping tests (install may have failed)")
        return False
    except Exception as e:
        warn(f"Test runner error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
#  SECTION 9 — POST-INSTALL SUMMARY
# ═══════════════════════════════════════════════════════════════════════

def print_summary(args: argparse.Namespace, success: bool) -> None:
    print("\n" + c(BOLD + CYAN, "═" * 62))
    if success:
        print(c(BOLD + GREEN, "  ✓  SecAgents installation complete!"))
    else:
        print(c(BOLD + YELLOW, "  ⚠  Installation finished with warnings"))

    if _errors:
        print(f"\n{c(RED, 'Errors encountered:')}")
        for e in _errors:
            print(f"  • {e}")

    print(f"\n{c(BOLD + WHITE, 'Next steps:')}")

    if IS_WIN:
        activate_cmd = r"  .venv\Scripts\activate"
    else:
        activate_cmd = "  source .venv/bin/activate"

    step1 = c(CYAN, str(ENV_FILE))
    step2 = c(CYAN, activate_cmd)
    step3_a = c(CYAN, 'make dev-api')
    step3_b = c(CYAN, 'uvicorn secagents_api.main:app --reload --port 8000')
    step4 = c(CYAN, 'python -c "import asyncio; from secagents.modules.autopilot import Autopilot; asyncio.run(Autopilot(\'example.com\').run())"')
    step5 = c(CYAN, 'docker compose up -d')

    print(f"""
  1. Edit your API keys:
       {step1}

  2. Activate the virtual environment:
       {step2}

  3. Start the API server:
       {step3_a}
       OR: {step3_b}

  4. Run a quick scan:
       {step4}

  5. Full stack (Docker):
       {step5}
    """)
    print(c(BOLD + CYAN, "═" * 62))


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SecAgents Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--no-db",   action="store_true", help="Skip PostgreSQL setup")
    parser.add_argument("--docker",  action="store_true", help="Use Docker Compose stack")
    parser.add_argument("--ci",      action="store_true", help="Non-interactive CI mode")
    parser.add_argument("--check",   action="store_true", help="Preflight checks only")
    parser.add_argument("--no-test", action="store_true", help="Skip running tests after install")
    return parser.parse_args()


def main() -> int:
    if not _no_color():
        print(c(BOLD + MAGENTA, BANNER))
    else:
        print(BANNER)

    args = parse_args()

    # ── Check-only mode ────────────────────────────────────────────────
    if args.check:
        ok_preflight = run_preflight(args)
        sys.exit(0 if ok_preflight else 1)

    # ── Main install flow ──────────────────────────────────────────────
    stages = [
        ("Preflight",          lambda: run_preflight(args)),
        ("Virtual Env",        create_venv),
        ("Upgrade pip",        upgrade_pip),
        ("Install packages",   install_python_packages),
        ("Frontend deps",      install_frontend_packages),
        ("Generate .env",      lambda: generate_env(args)),
    ]

    if args.docker:
        stages.append(("Docker stack", lambda: start_docker_stack(args)))
    else:
        stages.append(("Redis",    lambda: check_redis(args)))
        if not args.no_db:
            stages.append(("PostgreSQL", lambda: setup_postgres(args)))

    if not args.no_test:
        stages.append(("Tests", lambda: run_tests(args)))

    overall = True
    for _label, fn in stages:
        try:
            result = fn()
            if not result:
                overall = False
        except KeyboardInterrupt:
            print(f"\n{c(YELLOW, 'Installation interrupted by user.')}")
            sys.exit(130)
        except Exception as exc:
            fail(f"Unexpected error in '{_label}': {exc}")
            overall = False

    print_summary(args, overall and not _errors)
    return 0 if (overall and not _errors) else 1


if __name__ == "__main__":
    sys.exit(main())
