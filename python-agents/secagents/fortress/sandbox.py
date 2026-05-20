"""Module 9: Hermetic Docker execution with mounted results directory."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from secagents.infra.docker_mgr import ContainerConfig, DockerManager

RESULTS_DIR = Path("cog-ai-results")


class FortressSandbox:
    """
    All scanning/exploitation runs inside ephemeral Docker containers.
    Results persist to ./cog-ai-results/ with timestamps.
    """

    def __init__(
        self,
        results_dir: Path | None = None,
        image: str = "secagents/sandbox:latest",
    ):
        self.results_dir = results_dir or RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.run_dir = self.results_dir / time.strftime("%Y%m%d_%H%M%S")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.image = image
        self._config = ContainerConfig(
            image=image,
            workspace_mount=str(self.run_dir.resolve()),
            network="none",
        )

    @staticmethod
    def ensure_image(image: str = "secagents/sandbox:latest") -> bool:
        """Return True if image exists locally."""
        if not DockerManager.is_available():
            return False
        try:
            proc = subprocess.run(
                ["docker", "image", "inspect", image],
                capture_output=True,
                timeout=15,
                check=False,
            )
            return proc.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    @property
    def logs_dir(self) -> Path:
        d = self.run_dir / "logs"
        d.mkdir(exist_ok=True)
        return d

    @property
    def findings_dir(self) -> Path:
        d = self.run_dir / "findings"
        d.mkdir(exist_ok=True)
        return d

    async def run(self, command: str) -> tuple[int, str, str]:
        if not DockerManager.is_available():
            raise RuntimeError(
                "Docker is required for Fortress isolation. "
                "Install Docker or run with --no-sandbox (not recommended)."
            )
        if not self.ensure_image(self.image):
            raise RuntimeError(
                f"Fortress image '{self.image}' not found. "
                "Build: docker build -t secagents/sandbox:latest -f sandbox/Dockerfile sandbox/"
            )
        return await DockerManager.run_sandboxed(command, self._config)

    async def run_tool(self, tool: str, args: str) -> tuple[int, str, str]:
        return await self.run(f"{tool} {args}")

    def write_log(self, name: str, content: str) -> Path:
        path = self.logs_dir / name
        path.write_text(content)
        return path
