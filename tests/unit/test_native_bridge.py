"""Unit test suite for Native Core C++ Bridge and Python fallback functions."""

import pytest
from secagents.core.native import native_engine, NativeCore


def test_native_core_initialization():
    core = NativeCore()
    assert hasattr(core, "is_available")
    assert hasattr(core, "match_signature")
    assert hasattr(core, "probe_port")


def test_native_core_signature_matching():
    buffer = "Server: Apache/2.4.41 (Ubuntu) mod_ssl/2.4.41"
    pattern = r"Apache/\d+\.\d+"
    assert native_engine.match_signature(buffer, pattern) is True
    assert native_engine.match_signature(buffer, r"Nginx/\d+") is False


def test_native_core_port_probe():
    # Probe local host / port 80 or 443 with short timeout
    res = native_engine.probe_port("127.0.0.1", 80, timeout_ms=100)
    assert isinstance(res, dict)
    assert "open" in res
    assert "port" in res
    assert res["port"] == 80
    assert "engine" in res
