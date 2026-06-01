"""Docker container management for sandboxed execution."""

from __future__ import annotations

import asyncio
import shutil
import uuid
from dataclasses import dataclass


@dataclass
class ContainerConfig:
    image: str = "secagents/sandbox:latest"
    memory_limit: str = "2g"
    cpu_limit: float = 2.0
    network: str = "none"
    timeout: int = 120
    workspace_mount: str | None = None


class DockerManager:
    """Manages Docker containers for isolated tool execution."""

    @staticmethod
    def is_available() -> bool:
        return shutil.which("docker") is not None

    @staticmethod
    async def run_sandboxed(
        command: str, config: ContainerConfig | None = None
    ) -> tuple[int, str, str]:
        """Run a command in an ephemeral container. Returns (exit_code, stdout, stderr)."""
        cfg = config or ContainerConfig()
        name = f"secagents-{uuid.uuid4().hex[:8]}"

        cmd = [
            "docker",
            "run",
            "--rm",
            "--name",
            name,
            "--memory",
            cfg.memory_limit,
            f"--cpus={cfg.cpu_limit}",
            f"--network={cfg.network}",
        ]
        if cfg.workspace_mount:
            cmd.extend(["-v", f"{cfg.workspace_mount}:/workspace:ro"])
        cmd.extend([cfg.image, "sh", "-c", command])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=cfg.timeout)
            return proc.returncode or 0, stdout.decode(), stderr.decode()
        except asyncio.TimeoutError:
            await asyncio.create_subprocess_exec("docker", "kill", name)
            return 124, "", "Timeout exceeded"
        except Exception as e:
            return 1, "", str(e)

    @staticmethod
    async def build_image(dockerfile_path: str, tag: str = "secagents/sandbox:latest") -> bool:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "build",
            "-t",
            tag,
            "-f",
            dockerfile_path,
            ".",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0

    @staticmethod
    async def pull_image(image: str) -> bool:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "pull",
            image,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
