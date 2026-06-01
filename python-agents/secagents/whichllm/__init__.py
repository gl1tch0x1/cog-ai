"""whichllm: hardware-aware local model selection."""

from secagents.whichllm.hardware import (
    HardwareProfile,
    detect_hardware,
    recommend_local_model,
    setup_ollama,
)

__all__ = ["HardwareProfile", "detect_hardware", "recommend_local_model", "setup_ollama"]
