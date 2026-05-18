"""Base agent with structured output, confidence scoring, and retry logic."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    SUPERVISOR = "supervisor"
    PLANNER = "planner"
    RECON = "recon"
    WEB_SECURITY = "web_security"
    API_SECURITY = "api_security"
    VALIDATOR = "validator"
    REPORT = "report"


class AgentOutput(BaseModel):
    """Structured output from any agent."""
    agent: str
    role: AgentRole
    result: Any
    confidence: float  # 0.0 - 1.0
    reasoning: str = ""
    metadata: dict = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary with JSON serialization."""
        return json.loads(self.model_dump_json())


@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0


@dataclass
class AgentConfig:
    role: AgentRole
    name: str
    tools: list[str] = field(default_factory=list)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout_seconds: float = 300.0


class BaseAgent(ABC):
    """Abstract base for all SecAgents agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._system_prompt: str = ""
        self.logger = logging.getLogger(f"secagents.{config.name}")

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> AgentRole:
        return self.config.role

    @abstractmethod
    async def execute(self, task: dict) -> AgentOutput:
        """Execute the agent's primary function."""
        ...

    @abstractmethod
    def system_prompt(self) -> str:
        """Return the agent's system prompt."""
        ...

    async def run(self, task: dict) -> AgentOutput:
        """Execute agent with full lifecycle (no retry)."""
        self.logger.info(f"Starting execution: {task}")
        start_time = time.time()
        
        try:
            output = await asyncio.wait_for(
                self.execute(task),
                timeout=self.config.timeout_seconds
            )
            execution_time = (time.time() - start_time) * 1000
            output.execution_time_ms = execution_time
            self.logger.info(f"Execution completed in {execution_time:.2f}ms with confidence {output.confidence}")
            return output
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Agent execution timed out after {self.config.timeout_seconds}s"
            self.logger.error(error_msg)
            return AgentOutput(
                agent=self.name,
                role=self.role,
                result={},
                confidence=0.0,
                reasoning="Timeout during execution",
                error=error_msg,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Execution failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return AgentOutput(
                agent=self.name,
                role=self.role,
                result={},
                confidence=0.0,
                reasoning="Exception during execution",
                error=error_msg,
                execution_time_ms=execution_time,
            )

    async def run_with_retry(self, task: dict) -> AgentOutput:
        """Execute with retry logic and exponential backoff."""
        policy = self.config.retry_policy
        last_error: Exception | None = None
        last_output: AgentOutput | None = None

        for attempt in range(policy.max_retries + 1):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{policy.max_retries + 1}")
                output = await self.run(task)
                
                if output.error is None:
                    self.logger.info(f"Success on attempt {attempt + 1}")
                    return output
                
                last_output = output
                if attempt < policy.max_retries:
                    delay = policy.initial_delay * (policy.backoff_factor ** attempt)
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
                    await asyncio.sleep(delay)
            except Exception as e:
                last_error = e
                if attempt < policy.max_retries:
                    delay = policy.initial_delay * (policy.backoff_factor ** attempt)
                    self.logger.warning(f"Exception on attempt {attempt + 1}: {str(e)}, retrying in {delay}s")
                    await asyncio.sleep(delay)

        if last_output and last_output.error:
            return last_output
        
        error_msg = str(last_error) if last_error else "Unknown error after all retries"
        self.logger.error(f"Failed after {policy.max_retries + 1} attempts: {error_msg}")
        return AgentOutput(
            agent=self.name,
            role=self.role,
            result={},
            confidence=0.0,
            reasoning=f"Failed after {policy.max_retries + 1} attempts",
            error=error_msg,
        )

    def _format_output(
        self,
        result: Any,
        confidence: float,
        reasoning: str = "",
        metadata: Optional[dict] = None,
    ) -> AgentOutput:
        """Format agent output with confidence scoring."""
        if confidence < 0.0 or confidence > 1.0:
            self.logger.warning(f"Confidence {confidence} out of range, clamping to [0, 1]")
            confidence = max(0.0, min(1.0, confidence))
        
        return AgentOutput(
            agent=self.name,
            role=self.role,
            result=result,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata or {},
        )

    def _calculate_confidence(
        self,
        evidence_count: int,
        max_evidence: int = 10,
        base_confidence: float = 0.5,
    ) -> float:
        """Calculate confidence based on evidence."""
        normalized = min(evidence_count / max_evidence, 1.0)
        confidence = base_confidence + (normalized * (1.0 - base_confidence))
        return round(confidence, 2)
