"""Auto-healer: AI-powered retry with exponential backoff for failed phases."""

from __future__ import annotations

import asyncio
import time
from typing import Callable

from secagents.infra.logging_system import AuditLogger, AuditCategory


class AutoHealer:
    def __init__(self, max_retries: int = 3, base_delay: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._logger = AuditLogger.get_instance()

    async def heal(self, phase_fn: Callable, *args, **kwargs):
        """Retry a failed async phase with exponential backoff."""
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                result = await phase_fn(*args, **kwargs)
                if attempt > 0:
                    self._logger.info(f"Auto-healer: recovered on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_error = e
                delay = self.base_delay * (2**attempt)
                self._logger.audit(
                    AuditCategory.ERROR_OCCURRED,
                    f"Auto-healer attempt {attempt + 1}/{self.max_retries} failed: {e}",
                )
                await asyncio.sleep(delay)

        self._logger.error(f"Auto-healer exhausted retries: {last_error}")
        raise last_error  # type: ignore

    def heal_sync(self, fn: Callable, *args, **kwargs):
        """Retry a sync operation with linear backoff."""
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                time.sleep(self.base_delay * (attempt + 1))
        raise last_error  # type: ignore
