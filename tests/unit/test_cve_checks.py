import pytest
from secagents.modules.cve_checks import verify_finding, get_checks_for_url, is_static_asset

def test_is_static_asset():
    assert is_static_asset("http://example.com/style.css") is True
    assert is_static_asset("https://example.com/app.js?v=123") is True
    assert is_static_asset("https://example.com/api/users") is False

def test_get_checks_for_url():
    static_checks = get_checks_for_url("http://example.com/logo.png")
    assert all(c.header_only for c in static_checks)
    
    dynamic_checks = get_checks_for_url("http://example.com/api/v1/auth")
    assert len(dynamic_checks) > len(static_checks)

def test_verify_sqli():
    vulnerable, proof = verify_finding(
        check_key="sqli",
        response_body="Database error: You have an error in your SQL syntax near '1'",
        response_headers={},
        payload={}
    )
    assert vulnerable is True
    assert "DB error signature" in proof

    vulnerable, _ = verify_finding(
        check_key="sqli",
        response_body="Welcome to the dashboard",
        response_headers={},
        payload={}
    )
    assert vulnerable is False

def test_verify_xxe():
    vulnerable, proof = verify_finding(
        check_key="xxe",
        response_body="root:x:0:0:root:/root:/bin/bash",
        response_headers={},
        payload={}
    )
    assert vulnerable is True

def test_verify_rfi():
    from secagents.modules.cve_checks import RUN_CANARY
    vulnerable, proof = verify_finding(
        check_key="rfi",
        response_body=f"Included content from {RUN_CANARY}.com",
        response_headers={},
        payload={}
    )
    assert vulnerable is True

def test_verify_jwt_none():
    vulnerable, proof = verify_finding(
        check_key="jwt_none",
        response_body='{"status": "admin access granted"}',
        response_headers={"content-type": "application/json"},
        payload={}
    )
    assert vulnerable is True

def test_verify_csrf():
    vulnerable, proof = verify_finding(
        check_key="csrf",
        response_body='<html><body>Update successful</body></html>',
        response_headers={},
        payload={"method": "POST"}
    )
    assert vulnerable is True
