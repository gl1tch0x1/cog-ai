# Quick Start Guide — SecAgents v0.2.0

## 30-Second Setup

### Option 1: Docker (Easiest) ✅

```bash
# Clone and run
git clone https://github.com/your-org/secagents.git
cd secagents
docker compose up -d

# Access dashboard
open http://localhost:3000
```

**That's it!** Dashboard is live at `http://localhost:3000`

---

### Option 2: CLI (Single File)

```bash
# Download pre-built CLI
curl -L https://github.com/your-org/secagents/releases/download/v0.2.0/secagent-linux-x64 -o secagent
chmod +x secagent

# Run a scan
./secagent scan --target example.com --scope .example.com
```

---

### Option 3: Python Package

```bash
# Install from PyPI
pip install secagents

# Run from terminal
secagent scan --target example.com
```

---

## 5-Minute Full Setup

### Step 1: Prerequisites

```bash
# Check system
python --version        # 3.11+
cargo --version         # 1.70+
go version              # 1.21+
docker --version        # 24+
docker compose version  # 2.20+
```

### Step 2: Clone Repository

```bash
git clone https://github.com/your-org/secagents.git
cd secagents
cp .env.example .env
```

### Step 3: Start Services

```bash
# Using Docker Compose (recommended)
docker compose up -d

# Or manually
# Terminal 1: Database
docker run -d -e POSTGRES_PASSWORD=changeme postgres:16-alpine

# Terminal 2: Redis
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 3: API
cd api && uvicorn secagents_api.main:app --reload --port 8000

# Terminal 4: Frontend
cd frontend/apex && npm run dev

# Terminal 5: Rust Core
cd rust-core && cargo run --release
```

### Step 4: Access Dashboard

Open browser → **http://localhost:3000**

---

## First Security Scan (2 Minutes)

### Via Web Dashboard

1. **Login** (default: admin / admin)
2. **New Scan** → Enter target domain
3. **Configure** → Select scope (same domain / subdomains)
4. **Run** → Watch real-time progress
5. **Review** → Export findings

### Via CLI

```bash
# 1. Interactive scan
secagent scan --target example.com --interactive

# 2. Automated scan
secagent scan --target example.com \
  --scope ".example.com" \
  --depth 2 \
  --timeout 300 \
  --output-format json \
  --output findings.json

# 3. View findings
cat findings.json | jq '.findings[] | {title, severity, cvss}'
```

### Via Python API

```python
from secagents import Client

client = Client(api_url="http://localhost:8000")

# Start scan
scan = client.create_scan(
    target="example.com",
    scope=".example.com",
    depth=2
)

# Poll for results
findings = client.get_findings(scan.id)
for f in findings:
    print(f"{f.severity}: {f.title}")
```

---

## Configuration (3 minutes)

### 1. Set Your LLM Provider

Edit `.env`:

```bash
# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Or Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Or Local (Ollama)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

### 2. Configure Scope & Authorization

```bash
# In dashboard:
# Settings → Scan Configuration → Authorized Domains

ALLOWED_DOMAINS=example.com,.example.com,api.example.com
```

### 3. Set Database Connection

```bash
DATABASE_URL=postgresql+asyncpg://secagents:password@localhost:5432/secagents
REDIS_URL=redis://localhost:6379/0
```

---

## Running Your First Scan

### Scan Types

| Type | Scope | Time | Depth |
|------|-------|------|-------|
| **Quick** | Single domain | 5 min | 1 |
| **Standard** | Subdomains | 30 min | 2 |
| **Deep** | Full surface | 2+ hours | 3-4 |
| **Custom** | User-defined | Varies | 1-5 |

### Example: Quick Scan

```bash
secagent scan \
  --target example.com \
  --scan-type quick \
  --checks sqli,xss,csrf,idor \
  --timeout 300
```

### Example: Deep Scan with Chaining

```bash
secagent scan \
  --target example.com \
  --scope ".example.com" \
  --scan-type deep \
  --enable-chaining \
  --enable-pivot \
  --max-findings 50 \
  --output-format markdown \
  --output report.md
```

---

## Expected Output

### CLI Output

```
$ secagent scan --target example.com

🔍 SecAgents v0.2.0 — Starting Scan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PHASE 1] Reconnaissance
  ✓ Subdomains enumerated: 12
  ✓ Endpoints discovered: 347
  ✓ Technologies identified: Node.js, Express, PostgreSQL

[PHASE 2] Vulnerability Testing
  ✓ SQLi checks: 0 vulnerable
  ✓ XSS checks: 2 vulnerable
  ✓ CSRF checks: 1 vulnerable

[PHASE 3] Validation & PoC Generation
  ✓ Findings validated: 3/3
  ✓ PoCs generated: 3

[PHASE 4] Exploit Chain Analysis
  ✓ Attack chains identified: 1
  ✓ Chained severity: HIGH

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Results
  Critical: 0
  High: 2
  Medium: 1
  Low: 0

📁 Report: ./reports/example.com_20260520.md
```

### JSON Output Sample

```json
{
  "scan_id": "scan_abc123",
  "target": "example.com",
  "findings": [
    {
      "id": "find_001",
      "title": "Reflected XSS in /search",
      "severity": "high",
      "cve": "CWE-79",
      "cvss": 6.1,
      "target_url": "https://example.com/search?q=<injection>",
      "poc_url": "https://example.com/search?q=<script>alert(1)</script>",
      "proof_signal": "<script>alert(1)</script> reflected unencoded",
      "impact": "Attacker can execute arbitrary JavaScript in victim's browser",
      "remediation": "Use output encoding or Content-Security-Policy"
    }
  ]
}
```

---

## Common Tasks

### Update Target Scope

```bash
# Dashboard: Settings → Authorized Domains → Add domain
# OR CLI:
secagent config --add-domain newdomain.com
```

### Change LLM Provider

```bash
# Update .env
sed -i 's/LLM_PROVIDER=.*/LLM_PROVIDER=groq/' .env

# Restart API
docker compose restart api
```

### Export Findings

```bash
# JSON
secagent export --scan-id scan_abc123 --format json > findings.json

# Markdown
secagent export --scan-id scan_abc123 --format markdown > report.md

# CSV
secagent export --scan-id scan_abc123 --format csv > findings.csv
```

### View Scan History

```bash
# List all scans
secagent list-scans

# View specific scan
secagent view-scan --scan-id scan_abc123

# Latest findings
secagent list-findings --limit 10
```

---

## Troubleshooting

### Port Already in Use

```bash
# Change ports in docker-compose.yml
# Or find and kill process
lsof -i :8000
kill -9 <PID>
```

### Database Connection Error

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Reset database
docker compose down -v
docker compose up -d
```

### LLM Provider Error

```bash
# Verify API key
echo $OPENAI_API_KEY

# Test connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Scan Hanging

```bash
# Check logs
docker compose logs api

# Kill scan
secagent cancel-scan --scan-id <ID>

# Restart services
docker compose restart
```

---

## Next Steps

1. **📖 Read** [Full Documentation](README.md)
2. **🔧 Configure** [Advanced Settings](docs/CONFIGURATION.md)
3. **🔗 Learn** [API Reference](docs/API.md)
4. **🐛 Report** [Issues on GitHub](https://github.com/your-org/secagents/issues)
5. **💬 Join** [Discussion Community](https://github.com/your-org/secagents/discussions)

---

## Support

| Channel | Use For |
|---------|---------|
| 🐛 **GitHub Issues** | Bugs & feature requests |
| 📖 **Documentation** | How-to guides |
| 💬 **Discussions** | Questions & ideas |
| 📧 **security@secagents.io** | Security vulnerabilities |

---

## Key Concepts

### What is a "Finding"?

A validated vulnerability with:
- **PoC** — Proof-of-concept showing how to exploit it
- **Proof Signal** — Specific response confirming the vulnerability
- **CVSS** — Severity score (0-10)
- **Impact** — Real business risk
- **Remediation** — How to fix it

### What is "Exploit Chaining"?

Multiple vulnerabilities linked into an attack path:
```
SQL Injection → Credential Dump → Admin Bypass → RCE
```

### What is a "Scope"?

Authorization boundary for scanning:
```
Target: example.com
Scope: .example.com (includes subdomains)
      api.example.com, app.example.com, etc.
```

---

**Questions?** See [FAQ](docs/FAQ.md) or open a [GitHub Discussion](https://github.com/your-org/secagents/discussions).
