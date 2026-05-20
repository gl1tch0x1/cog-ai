"""Operational integrity: OS updates, tool self-update."""

from secagents.operational.integrity import (
    check_os_security_updates,
    check_and_apply_tool_update,
    OS_UPDATE_MESSAGE,
)

__all__ = [
    "check_os_security_updates",
    "check_and_apply_tool_update",
    "OS_UPDATE_MESSAGE",
]
