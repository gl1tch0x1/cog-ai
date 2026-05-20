"""Tests for operational integrity module."""

import pytest
from unittest.mock import patch, MagicMock

from secagents.operational.integrity import (
    check_os_security_updates,
    check_tool_update,
    _parse_version,
    OS_UPDATE_MESSAGE,
)


def test_parse_version():
    assert _parse_version("0.2.0") == (0, 2, 0)
    assert _parse_version("v1.10.3") == (1, 10, 3)


def test_os_check_skipped():
    ok, msg = check_os_security_updates(skip=True)
    assert ok is True
    assert "skipped" in msg.lower()


@patch("secagents.operational.integrity.fetch_latest_release_version", return_value="0.1.0")
def test_tool_update_available(mock_fetch):
    result = check_tool_update("0.2.0")
    assert result.update_available is False


@patch("secagents.operational.integrity.fetch_latest_release_version", return_value="9.0.0")
def test_tool_update_newer_remote(mock_fetch):
    result = check_tool_update("0.2.0")
    assert result.update_available is True
    assert "9.0.0" in result.remote_version


def test_os_update_message_defined():
    assert "security updates" in OS_UPDATE_MESSAGE.lower()
