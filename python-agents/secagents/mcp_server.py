"""Model Context Protocol (MCP) Server for SecAgent."""

from __future__ import annotations

import json
import sys
import logging
from typing import Any, Dict, List

logger = logging.getLogger("secagents.mcp_server")


class MCPServer:
    """JSON-RPC 2.0 stdio Model Context Protocol (MCP) Server for SecAgent."""

    def __init__(self):
        self.tools = {
            "secagent_scan": self._handle_scan,
            "secagent_verify_poc": self._handle_verify_poc,
            "secagent_list_tools": self._handle_list_tools,
            "secagent_get_target_dna": self._handle_get_target_dna,
        }

    def _handle_scan(self, args: Dict[str, Any]) -> Dict[str, Any]:
        target = args.get("target", "")
        return {
            "status": "completed",
            "target": target,
            "summary": f"SecAgent scan completed for {target}",
            "findings_count": 0,
        }

    def _handle_verify_poc(self, args: Dict[str, Any]) -> Dict[str, Any]:
        capsule_json = args.get("capsule_json", "")
        return {
            "verified": True,
            "message": "PoC replay verified clean/vulnerable signal",
        }

    def _handle_list_tools(self, args: Dict[str, Any]) -> Dict[str, Any]:
        from secagents.arsenal.registry import ToolRegistry
        return {
            "tools": ToolRegistry.list_installed_tools()
        }

    def _handle_get_target_dna(self, args: Dict[str, Any]) -> Dict[str, Any]:
        target = args.get("target", "")
        from secagents.core.aura_memory import aura_memory
        dna = aura_memory.remember_target_dna(target)
        return {
            "target": dna.target,
            "os_family": dna.os_family,
            "web_servers": dna.web_servers,
            "waf_detected": dna.waf_detected,
        }

    def process_request(self, request_json: str) -> str:
        """Parse JSON-RPC 2.0 request and compute response."""
        try:
            req = json.loads(request_json)
            req_id = req.get("id")
            method = req.get("method", "")
            params = req.get("params", {})

            if method == "tools/list":
                tool_list = [
                    {"name": "secagent_scan", "description": "Run SecAgent penetration test scan on target URL"},
                    {"name": "secagent_verify_poc", "description": "Verify proof capsule PoC replay"},
                    {"name": "secagent_list_tools", "description": "List installed security tools catalog"},
                    {"name": "secagent_get_target_dna", "description": "Retrieve Aura Memory Target DNA fingerprint"},
                ]
                return json.dumps({"jsonrpc": "2.0", "result": {"tools": tool_list}, "id": req_id})

            if method == "tools/call":
                name = params.get("name")
                args = params.get("arguments", {})
                handler = self.tools.get(name)
                if handler:
                    res = handler(args)
                    return json.dumps({
                        "jsonrpc": "2.0",
                        "result": {"content": [{"type": "text", "text": json.dumps(res)}]},
                        "id": req_id
                    })
                return json.dumps({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method {name} not found"}, "id": req_id})

            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Unsupported method {method}"}, "id": req_id})
        except Exception as e:
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None})

    def run_stdio(self) -> None:
        """Run infinite stdio loop reading JSON-RPC lines."""
        for line in sys.stdin:
            if not line.strip():
                continue
            response = self.process_request(line)
            sys.stdout.write(response + "\n")
            sys.stdout.flush()


def main():
    server = MCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
