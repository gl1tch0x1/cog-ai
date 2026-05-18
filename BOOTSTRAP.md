# BOOTSTRAP.md — System Initialization

## Overview

SecAgents initializes in a strict dependency order, with lazy loading to minimize startup time. Use `installer.py` for automated first-time setup.

## Boot Sequence

```
1. Environment Validation
   ├── Check Python 3.11+ (hard requirement)
   ├── Verify required packages (pydantic, httpx, openai, fastapi)
   ├── Validate API keys (at least 1 provider required)
   ├── Check disk space (minimum 2GB recommended)
   ├── Check network connectivity (warn-only)
   └── Check Docker availability (warn-only)

2. Provider Initialization (lazy — on first call)
   ├── Register available LLM providers from environment
   ├── Initialize AI Gateway routing table
   ├── Load provider performance history from MEMORY.md
   └── Set fallback chains per task type:
       ├── fast:      Groq → OpenAI → DeepSeek
       ├── balanced:  OpenAI → Anthropic → Gemini
       └── reasoning: Anthropic → OpenAI → DeepSeek

3. Service Registration
   ├── Initialize orchestrator (intent classifier + decomposer)
   ├── Register 7 agent definitions from AGENTS.md
   ├── Load tool schemas from TOOLS.md
   ├── Initialize dual-memory:
   │   ├── MEMORY.md → loaded at boot (persistent knowledge)
   │   └── MEM.md    → created fresh per session (runtime state)
   └── Start heartbeat monitor (5s interval)

4. Worker Pool Initialization
   ├── Spawn async worker coroutines (configurable: default 4)
   ├── Initialize Redis-backed task queue
   │   └── Fallback: in-memory asyncio.Queue if Redis unavailable
   ├── Register heartbeat for each worker
   └── Set idle timeout (30s before sleep mode)

5. Ready State
   └── System accepts requests via API or direct Python calls
```

## Dependency Order

```
environment → providers → orchestrator → agents → tools → workers → ready
```

## Lazy Loading Rules

| Component | When Initialized |
|-----------|-----------------|
| LLM providers | First API call to that provider |
| External tools | On demand (checked available at boot) |
| Browser/Playwright | Only if DOM-based checks requested |
| Docker sandbox | Only if `sandbox_exec` tool is invoked |
| MEM.md | Created fresh on every session start |
| MEMORY.md | Loaded once at boot, updated selectively |

## Recovery on Boot Failure

| Component | Failure Action |
|-----------|---------------|
| No API keys | Warn + allow local-only mode (Ollama) |
| No Docker | Warn + disable sandbox, run tools locally |
| No external tools | Warn + use built-in Python implementations |
| No Redis | Warn + use in-memory asyncio.Queue (single-node) |
| No PostgreSQL | Warn + use SQLite fallback (development only) |
| Python < 3.11 | Hard exit with upgrade instructions |

## Automated Setup

Run `installer.py` from the repo root for one-command setup:

```bash
python installer.py              # Interactive full install
python installer.py --ci         # Non-interactive (for CI/CD pipelines)
python installer.py --docker     # Use Docker Compose stack
python installer.py --check      # Preflight checks only (exit 0/1)
```

The installer handles: venv creation, package installation, PostgreSQL role + database + schema, `.env` generation with secure random secrets.

## Hot Reload (No Restart Required)

The system supports live reloading of:
- **Agent definitions** — AGENTS.md changes apply to next request
- **Tool schemas** — TOOLS.md changes apply to next tool call
- **User preferences** — USER.md changes apply immediately
- **Routing tables** — Provider performance updates apply per-call

## System Knowledge Files

| File | Role | Persistence |
|------|------|-------------|
| `IDENTITY.md` | Operational principles, boundaries | Static |
| `SOUL.md` | Strategic mindset, quality standards | Static |
| `AGENTS.md` | Agent definitions + LLM prompts | Hot-reloadable |
| `TOOLS.md` | Tool registry, schemas, policies | Hot-reloadable |
| `USER.md` | Dynamic user profile | Updated per session |
| `MEMORY.md` | Persistent cross-session learnings | Appended selectively |
| `MEM.md` | Runtime session state | Discarded on session end |
| `BOOTSTRAP.md` | This file — initialization guide | Static |
| `HEARTBEAT.md` | Health monitoring config | Static |
