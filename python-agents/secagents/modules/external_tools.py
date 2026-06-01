"""External security tool integrations via async subprocess."""

from __future__ import annotations

import asyncio
import shlex
import shutil
from dataclasses import dataclass


@dataclass
class ToolResult:
    tool: str
    success: bool
    output: list[str]
    raw: str = ""


class ExternalTools:
    """Async wrappers for common security tools."""

    TOOLS = {
        "subfinder": "subfinder -d {target} -silent",
        "httpx": "httpx -u {target} -silent -status-code -tech-detect",
        "naabu": "naabu -host {target} -top-ports 100 -silent -json",
        "katana": "katana -u {target} -silent -jc -d 3",
        "waybackurls": "echo {target} | waybackurls",
        "nuclei": "nuclei -u {target} -severity medium,high,critical -json",
        "arjun": "arjun -u {target} --stable -oJ /dev/stdout",
        "ffuf": "ffuf -u {target}/FUZZ -w {wordlist} -mc 200,301,302 -s",
        "ghauri": "ghauri -u {target} --batch --level 2",
        "nomore403": "nomore403 -u {target}",
    }

    @staticmethod
    def available() -> dict[str, bool]:
        return {name: shutil.which(name) is not None for name in ExternalTools.TOOLS}

    @staticmethod
    async def run(tool: str, target: str, timeout: int = 120, **kwargs) -> ToolResult:
        template = ExternalTools.TOOLS.get(tool)
        if not template:
            return ToolResult(tool=tool, success=False, output=[], raw=f"Unknown tool: {tool}")
        if not shutil.which(tool):
            return ToolResult(tool=tool, success=False, output=[], raw=f"{tool} not installed")

        safe_target = shlex.quote(target)
        safe_kwargs = {k: shlex.quote(str(v)) for k, v in kwargs.items()}
        try:
            cmd = template.format(target=safe_target, **safe_kwargs)
        except KeyError as e:
            return ToolResult(tool=tool, success=False, output=[], raw=f"Missing parameter: {e}")

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            lines = [line for line in stdout.decode().strip().split("\n") if line]
            return ToolResult(
                tool=tool, success=proc.returncode == 0, output=lines, raw=stdout.decode()
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return ToolResult(tool=tool, success=False, output=[], raw="Timeout")
        except Exception as e:
            return ToolResult(tool=tool, success=False, output=[], raw=str(e))

    @staticmethod
    async def run_parallel(tools: list[str], target: str) -> dict[str, ToolResult]:
        tasks = {t: ExternalTools.run(t, target) for t in tools}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        return {
            name: (
                r
                if isinstance(r, ToolResult)
                else ToolResult(tool=name, success=False, output=[], raw=str(r))
            )
            for name, r in zip(tasks.keys(), results)
        }
