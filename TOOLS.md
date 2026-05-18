# TOOLS.md — Tool Registry & Policies

## Tool Definitions

### Security Tools (External Binaries)

| Tool | Schema | Timeout | Retries | Rate Limit | Permission | Min Version |
|------|--------|---------|---------|------------|------------|-------------|
| subfinder | `{target: string}` | 60s | 2 | 10/min | recon_agent | 2.6+ |
| httpx | `{target: string, flags: string[]}` | 90s | 1 | 5/min | recon_agent | 1.3+ |
| nuclei | `{target: string, severity: string}` | 120s | 1 | 3/min | scan_agent | 3.0+ |
| naabu | `{target: string, ports: string}` | 60s | 2 | 5/min | recon_agent | 2.3+ |
| katana | `{target: string, depth: int}` | 90s | 1 | 5/min | recon_agent | 1.1+ |
| waybackurls | `{target: string}` | 60s | 2 | 10/min | recon_agent | latest |
| arjun | `{target: string}` | 60s | 1 | 5/min | recon_agent | 2.2+ |
| ffuf | `{target: string, wordlist: string}` | 120s | 1 | 3/min | scan_agent | 2.1+ |
| ghauri | `{target: string}` | 120s | 1 | 3/min | scan_agent | 1.3+ |
| nomore403 | `{target: string}` | 30s | 2 | 10/min | scan_agent | latest |
| interactsh | `{server: string}` | — | — | — | validator_agent | 1.1+ |
| playwright | `{url: string, action: string}` | 30s | 1 | 5/min | validator_agent | 1.44+ |

### Internal Tools

| Tool | Schema | Timeout | Permission |
|------|--------|---------|------------|
| memory_read | `{scope: string, query: string}` | 1s | all_agents |
| memory_write | `{scope: persistent\|runtime, key: string, value: any}` | 1s | orchestrator |
| http_request | `{url: string, method: string, headers: dict, body: any}` | 10s | security_agents |
| sandbox_exec | `{command: string, timeout: int}` | 120s | validator_agent |
| report_generate | `{findings: list, format: string}` | 30s | report_agent |
| poc_generate | `{finding: dict}` | 5s | validator_agent |
| scope_check | `{target: string, scope: list}` | 1s | planner_agent |

## Tool Installation

Install all optional external tools (Go-based):

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/tomnomnom/waybackurls@latest
go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest
pip install arjun
```

## Execution Policies

### Input Validation (Applied to Every Call)

- Schema validation against type definitions above
- Path traversal check: reject `../`, `%2e%2e`, null bytes
- Shell injection check: reject `;`, `|`, `&&`, backticks in non-shell parameters
- URL scheme check: allow only `http://` and `https://` in URL fields
- Domain scope check: reject targets outside `ALLOWED_DOMAINS`

### Output Limits

- Maximum response size: **1 MB per tool call**
- Responses exceeding limit are truncated with a warning
- JSON output is validated before being passed to agents

### Retry Policy

- Exponential backoff: `delay = base × 2^attempt` seconds
- Base delay: 2s
- Max retries: per-tool (see table above)
- Circuit breaker: **5 consecutive failures** → tool disabled for **60s**

### Observability

Every tool call is logged with:
```json
{
  "tool": "subfinder",
  "input_hash": "sha256:...",
  "duration_ms": 4231,
  "success": true,
  "output_size_bytes": 12048,
  "timestamp": "2026-05-17T09:00:00Z"
}
```

Failed calls also include `error_category` and `stderr`.

### Security Constraints

- All external tools execute in **Docker sandbox** by default (`--network none`, read-only mounts)
- No tool accesses secrets directly — injected via environment variables
- Tool outputs are HTML-escaped and null-byte-stripped before passing to agents
- Every invocation is recorded in the JSONL audit log
- Tool binaries must be in `PATH` — no dynamic download at runtime

### Timeout Handling

| Phase | Action |
|-------|--------|
| 80% of timeout | Soft warn logged |
| 100% of timeout | Process killed, `timeout` error returned |
| After kill | Resources released, error propagated to agent |

## Tool Registry (Python)

```python
from secagents.engine import ToolRegistry

registry = ToolRegistry()
available = registry.available_tools()
# Returns list of tool names that are in PATH and usable

result = await registry.call("subfinder", {"target": "example.com"})
# Returns: {"stdout": "...", "stderr": "", "exit_code": 0, "duration_ms": 4100}
```
