# SecAgents Complete Setup & Execution Guide

## Part 1: Initial Setup (5 minutes)

### 1.1 Clone & Environment
```bash
git clone https://github.com/secagents/secagents.git
cd secagents

# Create environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 1.2 Configure Environment
```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
# Set:
# - DATABASE_URL
# - REDIS_URL
# - LLM_API_KEY (OpenAI, Anthropic, etc.)
# - SECRET_KEY (generate: openssl rand -hex 32)
```

### 1.3 Initialize Database
```bash
# Create database
createdb secagents

# Run migrations
python -m alembic upgrade head

# Seed initial data
python -m secagents.scripts.seed_db

# Verify
psql secagents -c "SELECT COUNT(*) FROM alembic_version;"
```

---

## Part 2: Start Services (2 minutes)

### 2.1 Start Dependencies
```bash
# Terminal 1: PostgreSQL
psql secagents  # Verify it connects

# Terminal 2: Redis
redis-server

# Verify Redis
redis-cli ping  # Should return PONG
```

### 2.2 Start SecAgents Services
```bash
# Terminal 3: API Server
python -m secagents.api.main
# Should show: "Uvicorn running on http://0.0.0.0:8000"

# Terminal 4: Orchestrator
python -m secagents.core.orchestrator
# Should show: "Orchestrator started"

# Terminal 5: Frontend (optional)
cd frontend/apex && npm start
# Should show: "Listening on http://localhost:3000"
```

### 2.3 Verify Services
```bash
# In a new terminal
curl http://localhost:8000/health
# Should return:
# {"status": "healthy", "services": {...}}

curl http://localhost:8000/agents
# Should list all 7 agents with status "healthy"
```

---

## Part 3: Create Your First Scan (3 minutes)

### 3.1 Using CLI
```bash
# Create scan
secagents scan create \
  --target example.com \
  --scope ".example.com" \
  --scan-type full

# Get scan ID from output, e.g., "scan_20240101_001"

# Check status
secagents scan status scan_20240101_001

# Watch progress
secagents scan watch scan_20240101_001
```

### 3.2 Using Python SDK
```python
from secagents import SecAgents

client = SecAgents(api_key="your_api_key")

# Create scan
scan = client.scans.create(
    target="example.com",
    scope=".example.com",
    scan_type="full"
)

print(f"Scan ID: {scan.id}")

# Poll for results
import time
while True:
    status = client.scans.get(scan.id)
    print(f"Status: {status.status} ({status.progress}%)")
    
    if status.status == "completed":
        break
    
    time.sleep(5)

# Get findings
findings = client.scans.get_findings(scan.id)
for finding in findings:
    print(f"[{finding.severity}] {finding.type}: {finding.endpoint}")
```

### 3.3 Using cURL
```bash
# Create scan
SCAN_ID=$(curl -s -X POST http://localhost:8000/v1/scans \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "scope": ".example.com",
    "scan_type": "full"
  }' | jq -r '.id')

echo "Scan ID: $SCAN_ID"

# Check status
curl -s http://localhost:8000/v1/scans/$SCAN_ID \
  -H "Authorization: Bearer your_api_key" | jq '.status'

# Get findings
curl -s http://localhost:8000/v1/scans/$SCAN_ID/findings \
  -H "Authorization: Bearer your_api_key" | jq '.findings'
```

---

## Part 4: View Results (2 minutes)

### 4.1 Generate Report
```bash
# Generate Markdown report
secagents report generate \
  --scan-id scan_20240101_001 \
  --format markdown \
  --output report.md

# Generate PDF report
secagents report generate \
  --scan-id scan_20240101_001 \
  --format pdf \
  --output report.pdf
```

### 4.2 Via Web Dashboard
1. Open http://localhost:3000 in browser
2. Go to "Scans" tab
3. Click on your scan
4. View findings
5. Export report

### 4.3 Programmatically
```python
# Get findings
findings = client.scans.get_findings(scan.id)

# Filter by severity
critical = [f for f in findings if f.severity == "critical"]
high = [f for f in findings if f.severity == "high"]

print(f"Critical: {len(critical)}")
print(f"High: {len(high)}")

# Export to JSON
import json
with open("findings.json", "w") as f:
    json.dump([f.dict() for f in findings], f, indent=2)
```

---

## Part 5: Production Deployment (30 minutes)

### 5.1 Docker Deployment
```bash
# Build image
docker build -t secagents:latest .

# Run with Docker Compose
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs api
```

### 5.2 Kubernetes Deployment
```bash
# Create namespace
kubectl create namespace secagents

# Create secrets
kubectl create secret generic secagents-secrets \
  --from-literal=database-password=... \
  --from-literal=llm-api-key=... \
  -n secagents

# Deploy
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/orchestrator-deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify
kubectl get pods -n secagents
kubectl logs -n secagents -f deployment/secagents-api
```

### 5.3 Nginx Reverse Proxy
```nginx
upstream secagents_api {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://secagents_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Part 6: Monitoring & Maintenance

### 6.1 Check Health
```bash
# System health
curl http://localhost:8000/health | jq .

# Agent status
curl http://localhost:8000/agents | jq .

# Metrics
curl http://localhost:8000/v1/metrics | jq .

# Prometheus metrics
curl http://localhost:9090/metrics
```

### 6.2 View Logs
```bash
# API logs
tail -f logs/api.log

# Orchestrator logs
tail -f logs/orchestrator.log

# Agent logs
tail -f logs/agents/*.log

# Structured logs (JSON)
cat logs/secagents-*.log | jq 'select(.level == "ERROR")'
```

### 6.3 Database Maintenance
```bash
# Backup
pg_dump secagents > backup_$(date +%Y%m%d).sql

# Check table sizes
psql secagents -c "
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
  FROM pg_tables
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Vacuum & analyze
psql secagents -c "VACUUM ANALYZE;"
```

### 6.4 Cache Management
```bash
# Check Redis memory
redis-cli INFO memory

# Clear cache
redis-cli FLUSHDB

# Monitor connections
redis-cli CLIENT LIST
```

---

## Part 7: Common Tasks

### 7.1 Create API Key
```bash
# CLI
secagents auth create-key \
  --name "My Integration" \
  --expires-in 365

# API
curl -X POST http://localhost:8000/v1/auth/keys \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Integration",
    "expires_in_days": 365
  }' | jq '.api_key'
```

### 7.2 List Scans
```bash
# CLI
secagents scans list --status completed --limit 10

# API
curl http://localhost:8000/v1/scans \
  -H "Authorization: Bearer your_api_key" | jq '.scans'
```

### 7.3 Cancel Scan
```bash
# CLI
secagents scan cancel scan_20240101_001

# API
curl -X DELETE http://localhost:8000/v1/scans/scan_20240101_001 \
  -H "Authorization: Bearer your_api_key"
```

### 7.4 Export Findings
```bash
# As JSON
secagents findings export scan_20240101_001 --format json > findings.json

# As CSV
secagents findings export scan_20240101_001 --format csv > findings.csv

# As Excel
secagents findings export scan_20240101_001 --format xlsx > findings.xlsx
```

---

## Part 8: Advanced Configuration

### 8.1 Custom Payload Sets
```yaml
# payloads.yaml
web_vulnerabilities:
  xss:
    payloads:
      - "<img src=x onerror=alert(1)>"
      - "<svg onload=alert(1)>"
      - "<iframe src=javascript:alert(1)>"
  sqli:
    payloads:
      - "' OR '1'='1"
      - "' UNION SELECT NULL--"
      - "';DROP TABLE users--"
```

### 8.2 Custom Rules
```python
# custom_rules.py
CUSTOM_RULES = {
    "internal_api": {
        "pattern": r"api\.internal\.",
        "severity": "high",
        "description": "Internal API exposed"
    },
    "debug_endpoint": {
        "pattern": r"/debug|/admin|/test",
        "severity": "medium",
        "description": "Debug endpoint detected"
    }
}
```

### 8.3 Webhooks
```bash
# Create webhook
secagents webhooks create \
  --url https://your-domain.com/webhook \
  --events scan.completed,finding.discovered
```

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Cannot connect to database | Check `DATABASE_URL`, ensure PostgreSQL is running |
| Redis connection failed | Check `REDIS_URL`, ensure Redis is running |
| API key rejected | Verify key format: `Bearer <key>`, check expiration |
| Slow scans | Increase `MAX_CONCURRENT_SCANS`, scale workers |
| High memory | Reduce `MAX_PAYLOADS_PER_CHECK`, restart agents |
| Agents offline | Check agent logs, restart orchestrator |

---

## Getting Help

- **Documentation**: https://github.com/secagents/secagents/docs
- **Issues**: https://github.com/secagents/secagents/issues
- **Discord**: https://discord.gg/secagents
- **Email**: support@secagents.io

