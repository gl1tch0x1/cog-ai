"""Omni-LLM: universal provider interface and consensus."""

from secagents.llm.omni import OmniLLM, LLMMessage, LLMResponse
from secagents.llm.consensus import ConsensusEngine

__all__ = ["OmniLLM", "LLMMessage", "LLMResponse", "ConsensusEngine"]
