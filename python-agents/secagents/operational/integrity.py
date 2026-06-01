"""Module 1: Operational integrity and self-preservation."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple

import httpx

OS_UPDATE_MESSAGE = (
    "⚠️ Your OS has pending security updates. "
    "Please run 'sudo apt update && sudo apt upgrade -y' and re-run the tool."
)

GITHUB_REPO = os.environ.get("SECAGENT_GITHUB_REPO", "gl1tch0x1/cog-ai")
CURRENT_VERSION = "0.2.0"


class UpdateCheckResult(NamedTuple):
    update_available: bool
    local_version: str
    remote_version: str
    message: str


def check_os_security_updates(skip: bool = False) -> tuple[bool, str]:
    """
    Query package manager for pending security updates.
    Returns (ok_to_proceed, message).
    """
    if skip:
        return True, "OS check skipped (--skip-os-check)"

    system = platform.system().lower()
    if system == "windows":
        return True, "OS update check not applicable on Windows (skipped)"

    if system == "darwin":
        return True, "OS update check not automated on macOS (skipped)"

    # Linux: apt or dnf
    if shutil.which("apt-get"):
        try:
            subprocess.run(
                ["apt-get", "update", "-qq"],
                capture_output=True,
                timeout=120,
                check=False,
            )
            result = subprocess.run(
                ["apt-get", "-s", "upgrade"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            output = result.stdout + result.stderr
            # Block only when security-pocket / CVE-related upgrades are pending
            if re.search(
                r"security|debian-security|ubuntu.*security|CVE-\d+",
                output,
                re.IGNORECASE,
            ) and re.search(r"^\d+ upgraded|inst ", output, re.IGNORECASE | re.MULTILINE):
                return False, OS_UPDATE_MESSAGE
            return True, "No pending security-related apt upgrades detected"
        except (subprocess.TimeoutExpired, OSError) as e:
            return True, f"OS check inconclusive: {e}"

    if shutil.which("dnf"):
        try:
            result = subprocess.run(
                ["dnf", "check-update", "--security"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            # dnf returns 100 when updates available
            lines = [ln for ln in result.stdout.splitlines() if ln.strip() and not ln.startswith("Last")]
            if result.returncode == 100 or len(lines) > 2:
                return False, OS_UPDATE_MESSAGE.replace("apt", "dnf")
            return True, "No pending dnf security updates"
        except (subprocess.TimeoutExpired, OSError) as e:
            return True, f"OS check inconclusive: {e}"

    return True, "No supported package manager for OS update check"


def _parse_version(version: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", version)
    return tuple(int(p) for p in parts) if parts else (0,)


def fetch_latest_release_version(repo: str = GITHUB_REPO) -> str | None:
    """Fetch latest release tag from GitHub."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers={"Accept": "application/vnd.github+json"})
            if resp.status_code == 200:
                data = resp.json()
                tag = data.get("tag_name", "")
                return tag.lstrip("v")
    except httpx.HTTPError:
        pass
    return None


def check_tool_update(local_version: str = CURRENT_VERSION) -> UpdateCheckResult:
    remote = fetch_latest_release_version()
    if not remote:
        return UpdateCheckResult(False, local_version, local_version, "Could not fetch remote version")
    local_t = _parse_version(local_version)
    remote_t = _parse_version(remote)
    available = remote_t > local_t
    msg = f"Update available: {local_version} → {remote}" if available else f"Up to date ({local_version})"
    return UpdateCheckResult(available, local_version, remote, msg)


def _backup_before_update(root: Path) -> list[Path]:
    """Back up config.yaml and note venv path before pull."""
    backed: list[Path] = []
    for name in ("config.yaml", "config.yml", ".env"):
        src = root / name
        if src.exists():
            dst = root / f"{name}.bak"
            shutil.copy2(src, dst)
            backed.append(dst)
    return backed


def check_and_apply_tool_update(
    root: Path | None = None,
    auto_update: bool = True,
) -> tuple[bool, str]:
    """
    Compare local version to GitHub; optionally git pull.
    Returns (proceed, message).
    """
    root = root or Path.cwd()
    result = check_tool_update()
    if not result.update_available:
        return True, result.message

    if not auto_update:
        return True, f"{result.message} (auto-update disabled)"

    _backup_before_update(root)

    if (root / ".git").exists() and shutil.which("git"):
        try:
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=180,
                check=True,
            )
            return True, "Updation Completed, Now you may Proceed..."
        except subprocess.CalledProcessError as e:
            return True, f"Git pull failed: {e.stderr or e}; continuing with local version"

    if shutil.which("docker"):
        try:
            subprocess.run(
                ["docker", "pull", "ghcr.io/gl1tch0x1/cog-ai:latest"],
                capture_output=True,
                timeout=300,
                check=False,
            )
            return True, "Updation Completed, Now you may Proceed..."
        except subprocess.TimeoutExpired:
            pass

    return True, result.message
