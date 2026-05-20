<div align="center">

```
███████╗███████╗ ██████╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗
██╔════╝██╔════╝██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
███████╗█████╗  ██║     ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   
╚════██║██╔══╝  ██║     ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   
███████║███████╗╚██████╗██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   
╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝  
```

**Autonomous Offensive AI Framework for Red Teams & Security Researchers**

*Distributed cognitive system for autonomous red-teaming, vulnerability research, and AI safety audits.*

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Rust Core](https://img.shields.io/badge/core-rust-orange.svg)](https://www.rust-lang.org/)
[![Go Recon](https://img.shields.io/badge/recon-go-cyan.svg)](https://go.dev/)
[![Tests](https://img.shields.io/badge/tests-78%2B%20passing-brightgreen.svg)](https://github.com/gl1tch0x1/cog-ai)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

> ⚠️ **LEGAL DISCLAIMER** — SecAgent is designed exclusively for **authorized security testing, red team engagements, and vulnerability research** on systems you own or have explicit written permission to test. Unauthorized use against systems without permission is illegal. The authors assume no liability for misuse.

---

## Table of Contents

- [What Is SecAgent](#-what-is-secagent)
- [Capabilities](#-capabilities)
- [Architecture](#-architecture)
  - [1. System Architecture](#1-system-architecture--high-level-topology)
  - [2. Autonomous Scan Workflow](#2-autonomous-scan-workflow--end-to-end-lifecycle)
  - [3. Agent Architecture](#3-agent-architecture--internal-decision-logic)
  - [4. Data Flow](#4-data-flow--raw-finding-to-structured-report)
  - [5. System Boot Sequence](#5-system-boot-sequence--initialization-order)
  - [6. LLM Provider Routing](#6-llm-provider-routing--fallback-chain-logic)
- [Quick Start](#-quick-start)
- [Installation Guide](#-installation-guide)
  - [Prerequisites](#prerequisites)
  - [Method 1 — Docker (Recommended)](#method-1--docker-recommended)
  - [Method 2 — Manual Install](#method-2--manual-install)
- [Configuration](#-configuration)
- [Running Your First Scan](#-running-your-first-scan)
- [Usage Reference](#-usage-reference)
- [Example Output](#-example-output)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Contributing](#-contributing)
- [Troubleshooting](#-troubleshooting)

---

## ⚔️ What Is SecAgent

Traditional vulnerability scanners are **rigid, noisy, and context-blind.** They follow fixed paths, miss chained attack vectors, and flood you with thousands of false positives that waste your time.

**SecAgent is different.**

It is a **Distributed Cognitive System** — a polyglot, AI-native framework that uses autonomous agents to *reason* through an attack surface the way a skilled red-teamer does. It doesn't just run tools. It understands the target's technology stack, identifies high-value attack paths, pivots based on intermediate findings, and generates **deterministic, validated proof-of-concepts** for every confirmed vulnerability.

Built for:
- 🔴 **Red Teams** running full-scope engagements
- 🔬 **Security Researchers** conducting vulnerability research
- 🐛 **Bug Bounty Hunters** working on complex targets
- 🛡️ **Offensive Security Professionals** auditing AI systems and LLM pipelines

---

## 💀 Capabilities

| Module | Description |
|--------|-------------|
| 🧠 **Neural Orchestration** | Python-based brain that decomposes mission objectives into atomic execution DAGs |
| 🔍 **Autonomous Recon** | Go-powered concurrent subdomain enumeration, endpoint crawling, and banner grabbing |
| 🎯 **PoC Generation** | Auto-crafts deterministic Python/cURL proof-of-concepts to eliminate false positives |
| 🛡️ **AI Supply Chain Audits** | Detects weaponized AI configs (`.cursorrules`, `mcp.json`), prompt injection, and RAG exfiltration |
| 🦾 **Neural Filter** | 99% noise-reduction layer — findings are consensus-validated by specialist agents |
| ⛓️ **Exploit Chain Correlation** | Links individual findings into full multi-step attack paths |
| 🔁 **Autopilot Mode** | Fire-and-forget autonomous scanning from recon to report |
| 📊 **Structured Reporting** | Outputs validated JSON findings + executive-grade Markdown reports |

---

## 🏛️ Architecture

SecAgent is a polyglot microservice system engineered for horizontal scale and ultra-low latency. The sections below document every architectural layer — from the high-level system topology down to individual agent decision logic.

---

### 1. System Architecture — High-Level Topology

```mermaid
graph TB
    subgraph EXTERNAL["🌐 Control Plane (External)"]
        direction LR
        UI["🖥️ Next.js Dashboard<br/><i>Real-time findings UI</i>"]
        API["⚡ FastAPI REST Interface<br/><i>:8000 — WebSocket + REST</i>"]
    end

    subgraph ORCHESTRATION["⚙️ Orchestration Layer (Internal)"]
        direction LR
        REDIS[("🔴 Redis Pub/Sub<br/><i>Event Bus :6379</i>")]
        RUST["🦀 Rust Task Scheduler<br/><i>Async priority queue</i>"]
        DB[("🐘 PostgreSQL<br/><i>Audit Store :5432</i>")]
    end

    subgraph AGENTS["🧠 Agentic Execution Layer"]
        direction TB
        PLANNER["🎯 Planner Agent<br/><i>Mission → DAG decomposer</i>"]
        VALIDATOR["🔬 Validator Agent<br/><i>PoC generator + verifier</i>"]
        REPORTER["📊 Reporter Agent<br/><i>Finding formatter</i>"]
    end

    subgraph RECON["🔍 Go Recon Engine"]
        direction TB
        CRAWL["🕷️ Crawler<br/><i>Endpoint discovery</i>"]
        SUB["🌐 Subdomain Enum<br/><i>DNS brute + permutation</i>"]
        PORT["🔌 Port Scanner<br/><i>Banner grabbing</i>"]
    end

    subgraph LLM["🤖 LLM Gateway"]
        direction LR
        GPT["OpenAI GPT-4o"]
        CLAUDE["Anthropic Claude"]
        GROQ["Groq / DeepSeek"]
        LOCAL["Ollama (local)"]
    end

    FILTER["🦾 Neural Filter<br/><i>Consensus validator<br/>99% noise reduction</i>"]

    UI <-->|"HTTP / WebSocket"| API
    API -->|"Workflow commands"| REDIS
    REDIS <-->|"Strict JSON schema"| RUST
    RUST -->|"Priority queue dispatch"| PLANNER
    PLANNER -->|"Spawn sub-tasks"| VALIDATOR
    PLANNER -->|"Spawn sub-tasks"| REPORTER
    PLANNER <-->|"Reasoning calls"| LLM
    VALIDATOR <-->|"Validation calls"| LLM
    PLANNER -->|"Recon missions"| CRAWL
    PLANNER -->|"Recon missions"| SUB
    PLANNER -->|"Recon missions"| PORT
    CRAWL -->|"Raw endpoint data"| FILTER
    SUB -->|"Raw subdomain data"| FILTER
    PORT -->|"Banner + service data"| FILTER
    VALIDATOR -->|"PoC results"| FILTER
    FILTER -->|"Validated findings"| DB
    DB -->|"Query results"| API

    style EXTERNAL fill:#1a1a2e,stroke:#e94560,color:#fff
    style ORCHESTRATION fill:#16213e,stroke:#0f3460,color:#fff
    style AGENTS fill:#0f3460,stroke:#533483,color:#fff
    style RECON fill:#1a1a2e,stroke:#e94560,color:#fff
    style LLM fill:#16213e,stroke:#533483,color:#fff
    style FILTER fill:#533483,stroke:#e94560,color:#fff
```

---

### 2. Autonomous Scan Workflow — End-to-End Lifecycle

This is the full operational flow from the moment a scan is triggered to the final validated report.

```mermaid
sequenceDiagram
    autonumber
    actor Operator as 🔴 Operator / Red Teamer
    participant CLI as 🖥️ CLI / API
    participant Auto as 🎯 Autopilot Engine
    participant Recon as 🔍 Go Recon Engine
    participant Planner as 🧠 Planner Agent
    participant LLM as 🤖 LLM Gateway
    participant Scanners as 🛡️ Specialist Agents
    participant Filter as 🦾 Neural Filter
    participant Correlator as ⛓️ Correlator
    participant DB as 🐘 PostgreSQL

    Operator->>CLI: secagent scan --target example.com --depth deep
    CLI->>Auto: Initialise mission: target=example.com

    rect rgb(26, 26, 46)
        Note over Auto,Recon: PHASE 1 — RECONNAISSANCE
        Auto->>Recon: Enumerate subdomains, endpoints, banners
        Recon-->>Auto: Tech fingerprint (React 18, Go 1.21, PostgreSQL 15)
        Auto->>LLM: Classify target stack → identify high-value attack surface
        LLM-->>Auto: Priority attack paths: [API endpoints, Auth layer, Admin panel]
    end

    rect rgb(15, 52, 96)
        Note over Auto,Scanners: PHASE 2 — TARGETED SCANNING
        Auto->>Planner: Decompose mission into atomic scan tasks (DAG)
        Planner->>LLM: Generate specialist agent assignments
        LLM-->>Planner: Task DAG: [SQLi, SSRF, Auth bypass, IDOR, XSS, JWT audit]
        Planner->>Scanners: Dispatch parallel specialist agents
        Scanners-->>Planner: Raw finding stream (unvalidated)
    end

    rect rgb(83, 52, 131)
        Note over Planner,Filter: PHASE 3 — NEURAL VALIDATION
        Planner->>Filter: Submit raw findings for consensus validation
        Filter->>LLM: Generate deterministic PoC for each candidate
        LLM-->>Filter: PoC payloads
        Filter->>Scanners: Execute PoC against target
        Scanners-->>Filter: Execution proof signals
        Filter-->>Planner: High-confidence findings (confidence > 0.7)
    end

    rect rgb(233, 69, 96)
        Note over Planner,Correlator: PHASE 4 — EXPLOIT CHAIN CORRELATION
        Planner->>Correlator: Submit validated findings set
        Correlator->>LLM: Identify chained attack paths across findings
        LLM-->>Correlator: Attack chains: [SQLi → Cred dump → Admin bypass]
        Correlator-->>Planner: Structured attack path graph
    end

    Planner->>DB: Persist findings + attack chains + PoCs
    DB-->>CLI: Mission complete — structured report ready
    CLI-->>Operator: ✅ Report written → ./reports/example.com_20260520.md
```

---

### 3. Agent Architecture — Internal Decision Logic

How a single specialist agent reasons through a vulnerability hypothesis.

```mermaid
flowchart TD
    START(["🎯 Task Received\n<i>e.g. Test /v1/search for SQLi</i>"])

    START --> CLASSIFY["🧠 LLM Intent Classifier\n<i>Identify vuln type + attack vector</i>"]

    CLASSIFY --> PAYLOAD["⚙️ Payload Generator\n<i>Generate test payloads\nbased on tech fingerprint</i>"]

    PAYLOAD --> PROBE["🔌 HTTP Probe\n<i>Go HTTP client\nsends test requests</i>"]

    PROBE --> RESPONSE{"📡 Response Analyser\n<i>Anomaly detected?</i>"}

    RESPONSE -- "❌ No anomaly" --> ADJUST["🔄 Adjust Strategy\n<i>Try alternate payload\nor different parameter</i>"]
    ADJUST -->|"Max retries reached"| FALSE_POS(["⬜ FALSE POSITIVE\n<i>Discard finding</i>"])
    ADJUST -->|"Retry"| PAYLOAD

    RESPONSE -- "✅ Anomaly detected" --> POC["🎯 PoC Generator\n<i>Craft deterministic\nPython + cURL exploit</i>"]

    POC --> VERIFY["🔬 Execution Verifier\n<i>Run PoC and capture\nproof signal</i>"]

    VERIFY --> CONFIRMED{"✅ Proof Confirmed?"}

    CONFIRMED -- "❌ Not reproducible" --> FALSE_POS

    CONFIRMED -- "✅ Confirmed" --> SCORE["📊 CVSS Scorer\n<i>Calculate severity\nCVSS v3.1</i>"]

    SCORE --> FILTER_GATE["🦾 Neural Filter Gate\n<i>Consensus check\nacross 3 agents</i>"]

    FILTER_GATE --> CONSENSUS{"🤝 Consensus\n≥ 2/3 agents agree?"}

    CONSENSUS -- "❌ No consensus" --> FALSE_POS

    CONSENSUS -- "✅ Consensus reached" --> FINDING(["🔴 VALIDATED FINDING\n<i>Persisted to DB\nwith PoC attached</i>"])

    style START fill:#0f3460,stroke:#e94560,color:#fff
    style FINDING fill:#e94560,stroke:#fff,color:#fff
    style FALSE_POS fill:#2d2d2d,stroke:#666,color:#aaa
    style FILTER_GATE fill:#533483,stroke:#e94560,color:#fff
    style CONSENSUS fill:#533483,stroke:#e94560,color:#fff
```

---

### 4. Data Flow — Raw Finding to Structured Report

How raw scan data is transformed into an actionable, executive-grade report.

```mermaid
flowchart LR
    subgraph INPUT["📥 Raw Input Layer"]
        direction TB
        A1["HTTP Responses"]
        A2["DNS Records"]
        A3["Banner Strings"]
        A4["JS Source Analysis"]
    end

    subgraph ENRICH["🔬 Enrichment Pipeline"]
        direction TB
        B1["Tech Fingerprinting\n<i>Stack identification</i>"]
        B2["Parameter Extraction\n<i>Endpoints + inputs</i>"]
        B3["Auth Surface Mapping\n<i>Token, session, cookie</i>"]
    end

    subgraph ANALYSIS["🧠 AI Analysis Layer"]
        direction TB
        C1["Planner Agent\n<i>DAG decomposition</i>"]
        C2["Specialist Agents\n<i>SQLi, SSRF, IDOR, XSS…</i>"]
        C3["Neural Filter\n<i>Consensus validation</i>"]
    end

    subgraph OUTPUT["📊 Output Layer"]
        direction TB
        D1["JSON Findings\n<i>Structured, machine-readable</i>"]
        D2["Markdown Report\n<i>Executive-grade, human-readable</i>"]
        D3["Attack Chain Graph\n<i>Chained exploit paths</i>"]
        D4["PostgreSQL Audit Log\n<i>Persistent, queryable</i>"]
    end

    INPUT --> ENRICH
    ENRICH --> ANALYSIS
    ANALYSIS --> OUTPUT

    style INPUT fill:#1a1a2e,stroke:#e94560,color:#fff
    style ENRICH fill:#16213e,stroke:#0f3460,color:#fff
    style ANALYSIS fill:#0f3460,stroke:#533483,color:#fff
    style OUTPUT fill:#533483,stroke:#e94560,color:#fff
```

---

### 5. System Boot Sequence — Initialization Order

Exact dependency order SecAgent follows from cold start to accepting scan requests.

```mermaid
flowchart TD
    COLD(["🔌 Cold Start\n<i>python3 installer.py / docker compose up</i>"])

    COLD --> ENV["1️⃣ Environment Validation\n✔ Python 3.11+\n✔ API key present\n✔ Disk ≥ 2 GB\n✔ Network reachable"]

    ENV --> FAIL_ENV{"Pass?"}
    FAIL_ENV -- "❌ Python < 3.11" --> HARD_EXIT(["💀 Hard Exit\n<i>Upgrade Python</i>"])
    FAIL_ENV -- "❌ No API keys" --> LOCAL["⚠️ Warn → Local-only mode\n<i>Ollama fallback</i>"]
    FAIL_ENV -- "✅ All checks pass" --> PROVIDERS

    LOCAL --> PROVIDERS

    PROVIDERS["2️⃣ Provider Initialisation\n<i>Lazy — on first LLM call</i>\nRegister available providers\nBuild fallback routing table\nLoad performance history"]

    PROVIDERS --> SERVICES["3️⃣ Service Registration\n<i>Orchestrator + Intent Classifier\n7 Agent definitions loaded\nTool schemas registered\nDual memory system initialised</i>"]

    SERVICES --> DB_CHECK{"PostgreSQL\nreachable?"}
    DB_CHECK -- "❌ No" --> SQLITE["⚠️ SQLite fallback\n<i>Dev / single-node mode</i>"]
    DB_CHECK -- "✅ Yes" --> REDIS_CHECK

    SQLITE --> REDIS_CHECK

    REDIS_CHECK{"Redis\nreachable?"}
    REDIS_CHECK -- "❌ No" --> INMEM["⚠️ In-memory asyncio.Queue\n<i>Single-node fallback</i>"]
    REDIS_CHECK -- "✅ Yes" --> WORKERS

    INMEM --> WORKERS

    WORKERS["4️⃣ Worker Pool\n<i>Spawn 4 async coroutines\nRegister heartbeat monitors\nSet idle timeout: 30s</i>"]

    WORKERS --> DOCKER_CHECK{"Docker\navailable?"}
    DOCKER_CHECK -- "❌ No" --> NOSANDBOX["⚠️ Warn → Sandbox disabled\n<i>Tools run locally</i>"]
    DOCKER_CHECK -- "✅ Yes" --> READY

    NOSANDBOX --> READY

    READY(["✅ READY STATE\n<i>Accepting scan requests\nvia API or CLI</i>"])

    style COLD fill:#0f3460,stroke:#e94560,color:#fff
    style READY fill:#e94560,stroke:#fff,color:#fff
    style HARD_EXIT fill:#8b0000,stroke:#e94560,color:#fff
    style FAIL_ENV fill:#16213e,stroke:#e94560,color:#fff
    style DOCKER_CHECK fill:#533483,stroke:#e94560,color:#fff
    style REDIS_CHECK fill:#533483,stroke:#e94560,color:#fff
    style DB_CHECK fill:#533483,stroke:#e94560,color:#fff
```

---

### 6. LLM Provider Routing — Fallback Chain Logic

How SecAgent selects and falls back across LLM providers per task type.

```mermaid
flowchart TD
    TASK(["📥 Incoming Task\n<i>Classify by task type</i>"])

    TASK --> TYPE{"Task Type?"}

    TYPE -- "⚡ Fast classification\n(recon triage)" --> FAST_1["🟢 Try: Groq\n<i>Lowest latency</i>"]
    TYPE -- "⚖️ Balanced reasoning\n(vuln analysis)" --> BAL_1["🟢 Try: OpenAI GPT-4o"]
    TYPE -- "🧠 Deep reasoning\n(exploit chaining)" --> DEEP_1["🟢 Try: Anthropic Claude"]
    TYPE -- "🔒 Offline / air-gapped" --> LOCAL_1["🟢 Ollama (local)\n<i>No internet required</i>"]

    FAST_1 --> F1{"Available?"}
    F1 -- "✅" --> SUCCESS(["✅ Response returned"])
    F1 -- "❌ Rate limit / error" --> FAST_2["🟡 Fallback: OpenAI GPT-4o"]
    FAST_2 --> F2{"Available?"}
    F2 -- "✅" --> SUCCESS
    F2 -- "❌" --> FAST_3["🟠 Fallback: DeepSeek"]
    FAST_3 --> F3{"Available?"}
    F3 -- "✅" --> SUCCESS
    F3 -- "❌" --> FAIL_ALL

    BAL_1 --> B1{"Available?"}
    B1 -- "✅" --> SUCCESS
    B1 -- "❌" --> BAL_2["🟡 Fallback: Anthropic Claude"]
    BAL_2 --> B2{"Available?"}
    B2 -- "✅" --> SUCCESS
    B2 -- "❌" --> BAL_3["🟠 Fallback: Gemini 1.5 Pro"]
    BAL_3 --> B3{"Available?"}
    B3 -- "✅" --> SUCCESS
    B3 -- "❌" --> FAIL_ALL

    DEEP_1 --> D1{"Available?"}
    D1 -- "✅" --> SUCCESS
    D1 -- "❌" --> DEEP_2["🟡 Fallback: OpenAI GPT-4o"]
    DEEP_2 --> D2{"Available?"}
    D2 -- "✅" --> SUCCESS
    D2 -- "❌" --> DEEP_3["🟠 Fallback: DeepSeek"]
    DEEP_3 --> D3{"Available?"}
    D3 -- "✅" --> SUCCESS
    D3 -- "❌" --> FAIL_ALL

    LOCAL_1 --> L1{"Ollama running?"}
    L1 -- "✅" --> SUCCESS
    L1 -- "❌" --> FAIL_ALL

    FAIL_ALL(["💀 All providers failed\n<i>Task queued for retry\nOperator alerted</i>"])

    style TASK fill:#0f3460,stroke:#e94560,color:#fff
    style SUCCESS fill:#1a6b1a,stroke:#4caf50,color:#fff
    style FAIL_ALL fill:#8b0000,stroke:#e94560,color:#fff
    style TYPE fill:#16213e,stroke:#533483,color:#fff
```

---

**Why Polyglot?**

- **Rust** — Core scheduler: memory safety + microsecond-latency event handling under thousands of concurrent connections
- **Go** — Recon engine: native goroutines handle thousands of concurrent HTTP probes and DNS lookups with minimal overhead
- **Python** — Agent layer: world-class AI/ML ecosystem (LangChain, OpenAI SDK, Anthropic SDK) and rapid exploit development

---

## ⚡ Quick Start

> Get SecAgent running in under 5 minutes using Docker.

```bash
# 1. Clone the repository
git clone https://github.com/gl1tch0x1/cog-ai.git
cd cog-ai

# 2. Configure your environment
cp .env.example .env
nano .env  # Add at least one LLM API key (see Configuration section)

# 3. Run the automated installer with Docker
python3 installer.py --docker

# 4. Run your first scan
python3 -m secagents scan --target example.com --depth quick
```

That's it. The installer handles everything else: PostgreSQL setup, Redis, venv creation, dependency installation, and schema migration.

---

## 🛠️ Installation Guide

### Prerequisites

Before installing, ensure your system meets these requirements:

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| **OS** | Linux / macOS / Windows (WSL2) | WSL2 strongly recommended on Windows |
| **Python** | 3.11+ | **Note:** Python 3.13 requires **Rust** (https://rustup.rs/) to build dependencies like `pydantic-core`. |
| **Rust** | Required for Python 3.13 | Install via `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` |
| **RAM** | 8 GB | 16 GB recommended for full-stack mode |
| **CPU** | 4 cores | More cores = faster concurrent scanning |
| **Disk** | 2 GB free | For Docker images + scan artifacts |
| **Docker** | 20.10+ | Supports both `docker compose` (V2) and `docker-compose` (V1). |
| **Git** | Any | For cloning the repo |

**At least one LLM API key is required:**

| Provider | Env Variable | Notes |
|----------|-------------|-------|
| OpenAI | `OPENAI_API_KEY` | GPT-4o recommended |
| Anthropic | `ANTHROPIC_API_KEY` | Claude 3.5 Sonnet |
| Groq | `GROQ_API_KEY` | Fastest inference, free tier available |
| DeepSeek | `DEEPSEEK_API_KEY` | Cost-efficient option |
| Google | `GEMINI_API_KEY` | Gemini 1.5 Pro |
| Ollama | *(local)* | No API key needed — fully offline |

---

### Method 1 — Docker (Recommended)

The cleanest path. Runs the full stack (API, PostgreSQL, Redis, frontend) in isolated containers.

```bash
# Clone
git clone https://github.com/gl1tch0x1/cog-ai.git
cd cog-ai

# Configure environment
cp .env.example .env
nano .env  # Set your LLM API key(s)

# Install and launch full Docker stack
python3 installer.py --docker
```

The installer will:
1. Run preflight system checks
2. Create a Python virtual environment
3. Install all dependencies
4. Generate a secure `.env` with random DB password and JWT secret
5. Pull and start Docker containers (PostgreSQL, Redis, API, Frontend)
6. Apply database schema migrations
7. Run smoke tests
8. Print next steps

**Expected output:**
```
[01] Preflight System Checks
──────────────────────────────────────────────────────────
  ✓ Python 3.11.9 ✓
  ✓ Disk space: 45.2 GB free
  ✓ Docker found: /usr/bin/docker
  ✓ Network connectivity ✓

[02] Creating Python Virtual Environment
──────────────────────────────────────────────────────────
  ✓ Virtual environment created: /home/user/cog-ai/.venv

...

✓ SecAgents installation complete!
```

---

### Method 2 — Manual Install

Prefer full control? Use this path. Requires PostgreSQL and Redis already running on your machine.

**Step 1 — Clone and enter the repo**
```bash
git clone https://github.com/gl1tch0x1/cog-ai.git
cd cog-ai
```

**Step 2 — Configure environment**
```bash
cp .env.example .env
nano .env
```

**Step 3 — Run the installer**
```bash
# Skip Docker, keep your existing PostgreSQL
python3 installer.py

# Skip both Docker and local PostgreSQL (if using a remote DB)
python3 installer.py --no-db

# Run preflight checks only without making any changes
python3 installer.py --check
```

**Step 4 — Activate the virtual environment**
```bash
# Linux / macOS
source .venv/bin/activate

# Windows (WSL2)
source .venv/bin/activate

# Windows (native PowerShell)
.venv\Scripts\Activate.ps1
```

**Step 5 — Start the API server**
```bash
# Using Makefile
make dev-api

# Or directly
uvicorn secagents_api.main:app --reload --port 8000
```

**Step 6 — Verify services are up**
```bash
curl http://localhost:8000/health
# Expected: {"status": "operational", "version": "1.0.0"}
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure the following:

```bash
cp .env.example .env
```

```ini
# ── Database ──────────────────────────────────────────────────────────
DB_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql+asyncpg://secagents:your_secure_password_here@localhost:5432/secagents

# ── Redis (Task Queue) ────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── Authentication ────────────────────────────────────────────────────
JWT_SECRET=generate_a_long_random_string_here

# ── LLM Providers — Set at least ONE ─────────────────────────────────
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=sk-...
GEMINI_API_KEY=...

# ── Scope Control (REQUIRED) ──────────────────────────────────────────
# Only domains listed here will be scanned. This is a hard whitelist.
ALLOWED_DOMAINS=example.com,*.example.com

# ── Performance Tuning ────────────────────────────────────────────────
MAX_SCAN_DEPTH=3           # Go crawler recursion depth
MAX_CONCURRENT_AGENTS=4    # Parallel agent workers

# ── Integrations (Optional) ───────────────────────────────────────────
INTERACTSH_SERVER=         # OAST server for out-of-band detection
SLACK_WEBHOOK_URL=         # Alert channel for critical findings
JIRA_URL=                  # Ticket auto-creation
JIRA_API_TOKEN=
```

> 🔐 **Security Note:** Never commit `.env` to version control. The `.gitignore` excludes it by default. The `installer.py` generates cryptographically secure values for `DB_PASSWORD` and `JWT_SECRET` automatically.

**LLM Provider Selection Logic:**

SecAgent automatically routes requests to the best available provider based on task type:

| Task Type | Primary | Fallback Chain |
|-----------|---------|----------------|
| Fast scan classification | Groq | → OpenAI → DeepSeek |
| Balanced reasoning | OpenAI | → Anthropic → Gemini |
| Deep exploit reasoning | Anthropic | → OpenAI → DeepSeek |
| Offline / local | Ollama | *(no fallback)* |

**Universal key format:** Set `LLM_API_KEYS=sk-...,sk-ant-...` (comma-separated). SecAgent auto-detects the provider from each key prefix — no `--llm-provider` flag required.

---

## 🏗️ Production Platform Modules (v0.2)

SecAgent implements a strict multi-agent pipeline for authorized testing only:

| Codename | Module | Purpose |
|----------|--------|---------|
| **Pre-Flight** | `secagents/operational/` | OS security update check, GitHub self-update with config backup |
| **The Vault** | `secagents/vault/` | `.env` loading, color-coded key validation (🟢🟡🔴), masked logging |
| **Omni-LLM** | `secagents/llm/` | Provider-agnostic client + 2-of-N consensus for findings |
| **whichllm** | `secagents/whichllm/` | GPU/RAM detection, optimal Ollama model selection |
| **Hermes** | `secagents/hermes/` | SQLite memory, skill generation, post-scan retrospective |
| **The Arsenal** | `secagents/arsenal/` | SQLi, XSS, SSRF, IDOR, SSTI, XXE, CMDi, path traversal probes |
| **The Armada** | `secagents/armada/` | DAG planner, specialist agents, `--workers N` scaling |
| **The Crucible** | `secagents/crucible/` | PoC validation, exploit chaining, regression test registry |
| **Remediation** | `secagents/remediation/` | Auto-patch snippets, JSON/MD/HTML reports, Jira/Slack tickets |
| **The Fortress** | `secagents/fortress/` + `sandbox/Dockerfile` | Ephemeral Docker isolation, `./cog-ai-results/` persistence |
| **Intel** | `secagents/intel/` | Shodan + ProjectDiscovery Chaos enrichment |
| **Keyhacks** | `secagents/agents/keyhacks.py` | Leaked API key discovery + rate-limited validation |

### CLI Reference

```bash
# Full autonomous pipeline (recommended)
python3 -m secagents scan --target example.com --depth standard --workers 8

# Flags
#   --skip-os-check      Skip apt/dnf security update gate
#   --no-arsenal         Skip secondary heuristic probes (CVE engine only)
#   --insecure           Disable TLS verification (not recommended)
#   --no-sandbox         Disable Docker Fortress (not recommended)
#   --setup-local-llm    Run whichllm + Ollama model pull
#   --results-dir PATH   Output directory (default: ./cog-ai-results/)

python3 -m secagents vault --validate          # Color-coded API key status
python3 -m secagents preflight --skip-os-check
python3 -m secagents update --check-only
python3 -m secagents hardware --install       # whichllm + Ollama
python3 -m secagents keyhacks ./src/          # Leaked key scan (rate-limited)
python3 -m secagents worker                   # Redis worker for API workflows
python3 -m secagents update                   # Explicit self-update (not run during scan)
```

**Scope:** Every scan requires `ALLOWED_DOMAINS` in `.env`. Targets outside the list are rejected before any probing runs.

Build the Fortress sandbox image:

```bash
docker build -t secagents/sandbox:latest -f sandbox/Dockerfile sandbox/
```

---

## 🎯 Running Your First Scan

After installation and API server startup, here's a complete first-scan walkthrough.

**Verify the system is ready:**
```bash
python3 installer.py --check
# All checks must return ✓ before proceeding
```

**Method 1 — Python CLI (Recommended)**
```bash
# Activate your virtual environment first
source .venv/bin/activate

# Quick scan (recon + surface-level checks, ~5 min)
python3 -m secagents scan --target example.com --depth quick

# Standard scan (full recon + vuln analysis, ~20 min)
python3 -m secagents scan --target example.com --depth standard

# Deep scan (full autonomous chain including exploit correlation, ~60 min)
python3 -m secagents scan --target example.com --depth deep
```

**Method 2 — REST API**
```bash
# Trigger an autopilot scan via the API
curl -X POST http://localhost:8000/workflows/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "target": "example.com",
    "workflow_type": "autopilot",
    "config": {
      "depth": "standard",
      "allow_intrusive": false
    }
  }'

# Response
# {"workflow_id": "wf_3f9a1b...", "status": "queued", "estimated_time": "20min"}

# Poll for results
curl http://localhost:8000/workflows/wf_3f9a1b.../status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Method 3 — Full Docker Stack (Includes Dashboard)**
```bash
docker compose up -d
# Dashboard available at: http://localhost:3000
# API available at:       http://localhost:8000
# API Docs (Swagger):     http://localhost:8000/docs
```

---

## 📊 Example Output

When SecAgent identifies a vulnerability, it doesn't hand you a name and a CVSS score. It delivers a **fully validated exploit path.**

**Terminal Output (during scan):**
```
[RECON]  Subdomains discovered: api.example.com, admin.example.com, staging.example.com
[RECON]  Tech fingerprint: React 18, Go 1.21, PostgreSQL 15, nginx 1.24
[SCAN]   Testing 247 endpoints across 3 hosts
[AGENT]  SQLi candidate detected → api.example.com/v1/search?q=
[VALID]  Neural Filter: Generating PoC...
[VALID]  PoC confirmed: MySQL 8.0.35 version string returned
[CHAIN]  Correlating with auth bypass on /admin → Full access path identified
[REPORT] 1 critical, 2 high, 4 medium findings
[DONE]   Report written to: ./reports/example.com_20260520_143022.md
```

**Structured Finding (JSON):**
```json
{
  "finding": {
    "id": "FIND-001",
    "title": "Unauthenticated SQL Injection in Search Endpoint",
    "severity": "critical",
    "cwe": "CWE-89",
    "cvss": 9.9,
    "target_url": "https://api.example.com/v1/search",
    "poc_command": "curl 'https://api.example.com/v1/search?q=test%27+UNION+SELECT+null,user(),version()--'",
    "proof_signal": "MySQL 8.0.35-0ubuntu0.22.04.1",
    "impact": "Full database exfiltration including user credentials and PII.",
    "remediation": "Use parameterized queries via SQLAlchemy or prepared statements.",
    "false_positive": false,
    "validated_by": ["SQLAgent", "NeuralFilter", "CorrelationEngine"]
  }
}
```

**Executive Report (Markdown excerpt):**
```markdown
# Security Assessment: example.com
**Date:** 2026-05-20 | **Depth:** Standard | **Duration:** 18m 43s

## Summary
| Severity | Count | Validated |
|----------|-------|-----------|
| Critical | 1     | ✓ Yes     |
| High     | 2     | ✓ Yes     |
| Medium   | 4     | ✓ Yes     |
| Low      | 7     | ✓ Yes     |

## Critical Finding: SQL Injection — api.example.com/v1/search
**Proof:** MySQL 8.0.35 confirmed via UNION-based injection
**Attack Chain:** SQLi → Credential dump → Admin bypass → Full system access
**Fix:** Replace raw query construction with SQLAlchemy ORM parameterized queries
```

---

## 📁 Project Structure

```
cog-ai/
├── api/                        # FastAPI REST interface
│   ├── migrations/             # PostgreSQL schema migrations
│   └── secagents_api/          # API application code
│       ├── main.py             # Application entrypoint
│       ├── routes/             # Endpoint definitions
│       └── models/             # Pydantic schemas
│
├── python-agents/              # Core AI agent system
│   └── secagents/
│       ├── cli.py              # Command-line interface (python -m secagents)
│       ├── operational/        # OS/update checks
│       ├── vault/              # .env + key validation
│       ├── llm/                # Omni-LLM + consensus
│       ├── whichllm/           # Hardware-aware local LLM
│       ├── hermes/             # Learning loop memory
│       ├── arsenal/            # Built-in exploit probes
│       ├── armada/             # Agent swarm orchestration
│       ├── crucible/           # PoC validation + regression
│       ├── remediation/        # Auto-patch + reporting
│       ├── fortress/           # Docker sandbox wrapper
│       ├── intel/              # Shodan + Chaos
│       ├── pipeline/           # End-to-end scan runner
│       ├── modules/
│       │   ├── autopilot.py    # Autonomous scan orchestrator
│       │   ├── planner.py      # Mission decomposer (DAG builder)
│       │   ├── validator.py    # Neural filter + PoC generator
│       │   └── reporter.py     # Structured output generator
│       └── agents/             # Specialist agent definitions
│
├── go-services/                # Recon engine (Go)
│   ├── crawler/                # Endpoint discovery
│   ├── subdomain/              # Subdomain enumeration
│   └── portscan/               # Port and service scanning
│
├── rust-core/                  # Task scheduler + event bus (Rust)
│
├── frontend/apex/              # Next.js dashboard
│
├── deployments/k8s/            # Kubernetes manifests
│
├── tests/
│   ├── unit/                   # Unit tests (pytest)
│   └── integration/            # Integration tests
│
├── docs/                       # Extended documentation
├── templates/                  # Report templates
│
├── .env.example                # Environment template (all supported keys)
├── sandbox/Dockerfile          # Fortress isolation image
├── cog-ai-results/             # Scan output (gitignored)
├── docker-compose.yml          # Full stack Docker Compose
├── installer.py                # Automated setup script
├── Makefile                    # Common dev commands
├── Cargo.toml                  # Rust workspace manifest
├── pytest.ini                  # Test configuration
│
├── AGENTS.md                   # Agent definitions + LLM prompts
├── TOOLS.md                    # Tool registry and schemas
├── BOOTSTRAP.md                # System initialization guide
├── CONTRIBUTING.md             # Contribution guidelines
├── SECURITY.md                 # Security policy
└── CHANGELOG.md                # Version history
```

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Agent Runtime** | Python 3.11+ | LLM reasoning, exploit logic, orchestration |
| **Recon Engine** | Go 1.21+ | Concurrent HTTP probing, subdomain enum |
| **Task Scheduler** | Rust (Tokio) | Async event bus, microsecond task dispatch |
| **API** | FastAPI | REST interface, WebSocket scan streaming |
| **Dashboard** | Next.js / TypeScript | Real-time findings UI |
| **Database** | PostgreSQL 15 | Persistent audit store |
| **Task Queue** | Redis 7 | Pub/Sub event bus, worker coordination |
| **AI Providers** | OpenAI / Anthropic / Groq / DeepSeek / Gemini / Ollama | LLM reasoning layer |
| **Containerization** | Docker / Docker Compose | Service isolation |
| **Orchestration** | Kubernetes | Production-scale deployment |

---

## 🤝 Contributing

SecAgent is open-source. Contributions that enhance the reasoning engine, add new specialist agents, or improve the recon pipeline are welcome.

**Before submitting a PR:**

```bash
# Run the full test suite — all tests must pass
python3 -m pytest tests/ -v --tb=short

# Lint your code
python3 -m ruff check python-agents/
python3 -m mypy python-agents/secagents/

# Test your changes against the installer
python3 installer.py --check
```

**Contribution areas:**

- New specialist agents (SSRF, XXE, IDOR, OAuth2, GraphQL)
- LLM provider integrations
- Recon module improvements (Go)
- Dashboard features (Next.js)
- CI/CD and deployment tooling

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines and the architectural boundaries each component must respect.

---

## 🔍 Troubleshooting

**PostgreSQL connection refused**
```bash
# Check if PostgreSQL is running
sudo service postgresql status

# Start it
sudo service postgresql start

# Or use Docker
docker run -d --name secagents-postgres \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 postgres:15-alpine
```

**Redis not reachable**
```bash
# Start Redis via Docker (installer does this automatically)
docker run -d --name secagents-redis \
  -p 6379:6379 redis:7-alpine

# Verify
redis-cli ping
# Expected: PONG
```

**Python version error**
```bash
# Check your Python version
python3 --version
# Must be 3.11 or higher

# On Ubuntu/Debian
sudo apt install python3.11 python3.11-venv
```

**`secagents` module not found after install**
```bash
# Make sure you've activated the virtual environment
source .venv/bin/activate

# Verify the package is installed
pip show secagents
```

**Installer fails mid-way**
```bash
# Run preflight diagnostics first
python3 installer.py --check

# Re-run with verbose output — each stage is numbered and logged
python3 installer.py --no-test  # Skip tests if just debugging setup
```

**API returns 401 Unauthorized**
```bash
# Generate a valid JWT token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

For issues not covered here, open a [GitHub Issue](https://github.com/gl1tch0x1/cog-ai/issues) with your OS, Python version, and the full installer output.

---

## 📝 Citation

If you use SecAgent in your research or security engagements, please cite the tool as follows:

```bibtex
@software{secagent2025,
  author = {gl1tch0x1},
  title = {SeAgent: Autonomous Offensive AI Framework for Red Teams & Security Researchers},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub},
  howpublished = {\url{https://github.com/gl1tch0x1/cog-ai}},
  url = {https://github.com/gl1tch0x1/cog-ai}
}
```

## 🙏 Acknowledgments

This project has been made possible through the support and inspiration of the offensive security research community. Special thanks to:
- The developers of **sec**, **bbh-ai**, and **apex** for the foundational modules.
- All contributors who have submitted bug reports, feature requests, and pull requests.
- Security researchers who provide the vulnerability research that fuels our specialist agents.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**SecAgent: Elite Intelligence. Industrial Power.**

*Built for professionals who think in attack paths, not checklists.*

`[ MISSION COMPLETE ]`

---

[Report a Bug](https://github.com/gl1tch0x1/cog-ai/issues) · [Request a Feature](https://github.com/gl1tch0x1/cog-ai/issues) · [Security Policy](SECURITY.md)

</div>
