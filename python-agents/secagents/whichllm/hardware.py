"""Module 3: Resource awareness and local LLM optimization."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class HardwareProfile:
    cpu_cores: int
    ram_gb: float
    gpu_vram_gb: float
    has_gpu: bool
    os_name: str

    def summary(self) -> str:
        gpu = f"{self.gpu_vram_gb:.1f}GB VRAM" if self.has_gpu else "no discrete GPU"
        return f"{self.cpu_cores} cores, {self.ram_gb:.1f}GB RAM, {gpu}"


def detect_hardware() -> HardwareProfile:
    cpu_cores = os.cpu_count() or 4
    ram_gb = 8.0
    try:
        import psutil  # optional

        ram_gb = psutil.virtual_memory().total / (1024**3)
    except ImportError:
        if platform.system() == "Linux":
            try:
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kb = int(line.split()[1])
                            ram_gb = kb / (1024**2)
                            break
            except OSError:
                pass

    gpu_vram = 0.0
    has_gpu = False
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if out.stdout.strip():
                has_gpu = True
                gpu_vram = float(out.stdout.strip().split("\n")[0]) / 1024
        except (subprocess.TimeoutExpired, ValueError):
            pass

    return HardwareProfile(
        cpu_cores=cpu_cores,
        ram_gb=ram_gb,
        gpu_vram_gb=gpu_vram,
        has_gpu=has_gpu,
        os_name=platform.system(),
    )


def recommend_local_model(profile: HardwareProfile | None = None) -> tuple[str, str]:
    """Return (runtime, model_name) for ollama."""
    p = profile or detect_hardware()
    if p.has_gpu and p.gpu_vram_gb >= 20:
        return "ollama", "llama3.1:70b"
    if p.has_gpu and p.gpu_vram_gb >= 8:
        return "ollama", "llama3.1:8b"
    if p.ram_gb >= 16:
        return "ollama", "llama3.2:3b"
    if p.ram_gb >= 8:
        return "ollama", "phi3:mini"
    return "ollama", "tinyllama"


def setup_ollama(model: str | None = None, pull: bool = True) -> tuple[bool, str]:
    """Install/pull recommended Ollama model for detected hardware."""
    if not shutil.which("ollama"):
        return False, "Ollama not installed. Visit https://ollama.com/download"

    _, model = recommend_local_model() if not model else ("ollama", model)
    if not pull:
        os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")
        return True, f"Recommended model: {model}"

    try:
        subprocess.run(
            ["ollama", "pull", model], capture_output=True, text=True, timeout=600, check=True
        )
        os.environ["OLLAMA_MODEL"] = model
        return True, f"Pulled {model} via Ollama"
    except subprocess.CalledProcessError as e:
        return False, f"ollama pull failed: {e.stderr or e}"
    except subprocess.TimeoutExpired:
        return False, "ollama pull timed out"
