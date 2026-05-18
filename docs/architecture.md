# Architecture

## System Overview

SecAgents uses a polyglot architecture optimized for each concern:

- **Rust** for deterministic, high-throughput workflow orchestration
- **Go** for concurrent network I/O (recon, scanning)
- **Python** for LLM integration and agent reasoning
- **TypeScript** for the interactive dashboard

## Communication

```
Frontend ←HTTP→ FastAPI ←Redis→ Rust Core ←Redis→ Go Services
                   ↕                ↕
              PostgreSQL        Python Agents
```

- FastAPI serves as the control plane
- Redis acts as the message bus between services
- Rust core manages workflow state and dispatches tasks
- Go services execute high-performance network operations
- Python agents handle LLM-guided decision making

## Data Flow

1. User creates target via API/UI
2. Workflow starts → Rust engine creates task graph
3. Scheduler dispatches tasks to appropriate services
4. Go services perform recon, return results via Redis
5. Python agents analyze results, generate payloads, test
6. Validator agent confirms findings
7. Report agent generates output
8. Results stored in PostgreSQL, surfaced in APEX

## Security Model

- All tool execution happens in sandboxed containers
- Policy engine validates every request against scope
- Audit log captures all state transitions
- Secrets never stored in code — env vars only
