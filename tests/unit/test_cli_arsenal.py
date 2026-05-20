"""Tests for CLI argument parsing, arsenal probes, and missing modules."""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

os.environ.setdefault("ALLOWED_DOMAINS", "example.com,*.example.com")
os.environ.setdefault("OLLAMA_HOST", "")


# ─── CLI Tests ───────────────────────────────────────────────────────────────

class TestCLI:
    def test_build_parser(self):
        from secagents.cli import build_parser
        parser = build_parser()
        # Scan command
        args = parser.parse_args(["scan", "--target", "example.com", "--depth", "quick"])
        assert args.command == "scan"
        assert args.target == "example.com"
        assert args.depth == "quick"
        assert args.workers == 4  # default

    def test_scan_depth_choices(self):
        from secagents.cli import build_parser
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["scan", "--target", "x.com", "--depth", "invalid"])

    def test_vault_command(self):
        from secagents.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["vault", "--validate"])
        assert args.command == "vault"
        assert args.validate is True

    def test_keyhacks_command(self):
        from secagents.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["keyhacks", "/tmp/src"])
        assert args.command == "keyhacks"
        assert args.paths == ["/tmp/src"]

    def test_worker_command(self):
        from secagents.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["worker"])
        assert args.command == "worker"


# ─── Arsenal Tests ───────────────────────────────────────────────────────────

class TestArsenal:
    @pytest.mark.asyncio
    async def test_scan_url_detects_sqli(self):
        from secagents.arsenal.exploits import ArsenalScanner
        scanner = ArsenalScanner(timeout=5.0, verify_ssl=True)

        mock_resp = MagicMock()
        mock_resp.text = "You have an error in your SQL syntax near '1'"
        mock_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("secagents.arsenal.exploits.httpx.AsyncClient", return_value=mock_client):
            results = await scanner.scan_url("https://example.com/search?q=test")

        # Should detect SQLi pattern
        sqli_results = [r for r in results if r.vuln_type == "sqli"]
        assert len(sqli_results) > 0
        assert "sql syntax" in sqli_results[0].evidence.lower() or "Matched pattern" in sqli_results[0].evidence

    @pytest.mark.asyncio
    async def test_scan_url_no_false_positive_on_clean(self):
        from secagents.arsenal.exploits import ArsenalScanner
        scanner = ArsenalScanner()

        mock_resp = MagicMock()
        mock_resp.text = "<html><body>Welcome to our site</body></html>"
        mock_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("secagents.arsenal.exploits.httpx.AsyncClient", return_value=mock_client):
            results = await scanner.scan_url("https://example.com/")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_scan_url_handles_http_error(self):
        import httpx
        from secagents.arsenal.exploits import ArsenalScanner
        scanner = ArsenalScanner()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("secagents.arsenal.exploits.httpx.AsyncClient", return_value=mock_client):
            results = await scanner.scan_url("https://example.com/")

        assert results == []  # Graceful handling, no crash


# ─── Rate Limiter Tests ──────────────────────────────────────────────────────

class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_async_rate_limiter_allows_requests(self):
        from secagents.infra.rate_limiting import TokenBucket
        bucket = TokenBucket(capacity=5, refill_per_sec=10)
        # Should allow 5 immediate requests
        for _ in range(5):
            assert await bucket.consume() is True
        # 6th should fail
        assert await bucket.consume() is False

    @pytest.mark.asyncio
    async def test_async_rate_limiter_wait_and_consume(self):
        import asyncio
        from secagents.infra.rate_limiting import TokenBucket
        bucket = TokenBucket(capacity=1, refill_per_sec=100)
        await bucket.consume()  # drain
        # Should wait and then succeed
        await asyncio.wait_for(bucket.wait_and_consume(), timeout=1.0)


# ─── Scope Tests (additional edge cases) ─────────────────────────────────────

class TestScopeEdgeCases:
    def test_ip_address_rejected(self):
        from secagents.infra.scope import normalize_target
        # IPs should normalize but may not match domain patterns
        assert normalize_target("http://192.168.1.1/path") == "192.168.1.1"

    def test_port_stripped(self):
        from secagents.infra.scope import normalize_target
        assert normalize_target("https://example.com:8443/api") == "example.com"

    def test_empty_target(self):
        from secagents.infra.scope import normalize_target
        assert normalize_target("") == ""
        assert normalize_target("   ") == ""


# ─── Armada Tests ─────────────────────────────────────────────────────────────

class TestArmada:
    def test_plan_mission_creates_graph(self):
        from secagents.armada.swarm import ArmadaOrchestrator
        armada = ArmadaOrchestrator(workers=2)
        graph = armada.plan_mission("example.com", "quick")
        assert len(graph.tasks) == 4
        assert graph.tasks[0].depends_on == []

    @pytest.mark.asyncio
    async def test_execute_with_handler(self):
        from secagents.armada.swarm import ArmadaOrchestrator

        armada = ArmadaOrchestrator(workers=2)
        called = []

        async def mock_handler(context, action):
            called.append(action)
            return {"findings": []}

        armada.register_handler("subdomain", mock_handler)
        armada.register_handler("web_crawl", mock_handler)
        armada.register_handler("validator", mock_handler)

        graph = armada.plan_mission("example.com", "quick")
        results = await armada.execute(graph, {"target": "example.com"})
        assert len(called) > 0
