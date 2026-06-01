# SecAgents Troubleshooting Guide

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Runtime Issues](#runtime-issues)
3. [Agent Issues](#agent-issues)
4. [Performance Issues](#performance-issues)
5. [API Issues](#api-issues)
6. [Debugging Tools](#debugging-tools)

---

## Installation Issues

### Python Package Conflicts
**Problem:** `pip install` fails with dependency conflicts

**Solution:**
```bash
# Create fresh virtual environment
python -m venv venv_clean
source venv_clean/bin/activate

# Install with specific resolver
pip install --use-deprecated=legacy-resolver -r requirements.txt

# Or use Poetry
poetry install
```

### PostgreSQL Connection Failed
**Problem:** `psycopg2.OperationalError: could not connect to server`

**Diagnosis:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres

# Check port
netstat -tulpn | grep 5432
```

**Solution:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Set password
sudo -u postgres psql
ALTER USER postgres WITH PASSWORD 'new_password';
\q

# Update connection string in .env
DATABASE_URL="postgresql://postgres:new_password@localhost:5432/secagents"
```

### Redis Connection Failed
**Problem:** `redis.ConnectionError: Error 111 connecting to localhost:6379`

**Diagnosis:**
```bash
# Check Redis is running
redis-cli ping

# Check port
netstat -tulpn | grep 6379
```

**Solution:**
```bash
# Start Redis
redis-server

# Or using systemd
sudo systemctl start redis-server

# Test connection
redis-cli -h localhost -p 6379 ping
# Should return PONG
```

### Missing Python Modules
**Problem:** `ModuleNotFoundError: No module named 'secagents'`

**Solution:**
```bash
# Install in editable mode
pip install -e python-agents/

# Verify installation
python -c "import secagents; print(secagents.__version__)"
```

---

## Runtime Issues

### API Won't Start
**Problem:** `RuntimeError: Can't connect to running event loop`

**Solution:**
```python
# In main.py, ensure event loop setup
import asyncio

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Worker Pool Not Processing Tasks
**Problem:** Tasks stuck in `queued` state

**Diagnosis:**
```bash
# Check worker status
curl http://localhost:8000/workers

# Check task queue length
redis-cli LLEN "task_queue"

# Check worker logs
tail -f logs/workers.log
```

**Solution:**
```bash
# Restart workers
pkill -f "secagents.core.workers"
python -m secagents.core.workers &

# Clear stuck tasks
redis-cli DEL "task_queue"

# Check for deadlocks
ps aux | grep secagents | grep defunct
```

### Memory Leak
**Problem:** Memory usage growing over time

**Diagnosis:**
```bash
# Monitor memory
watch -n 1 'ps aux | grep python | grep secagents'

# Profile memory
python -m memory_profiler main.py

# Check for unclosed connections
grep -r "\.close()" python-agents/
```

**Solution:**
```python
# Use context managers for all resources
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()

# Explicitly close connections
pool.close()
await pool.wait_closed()

# Disable request logging if verbose
logging.getLogger("aiohttp.web").setLevel(logging.WARNING)
```

---

## Agent Issues

### Agent Not Responding
**Problem:** Agent timeout or no response

**Diagnosis:**
```bash
# Check agent status
curl http://localhost:8000/agents/web_security

# Check agent logs
tail -f logs/agents/web_security.log

# Test agent directly
python -c "
import asyncio
from secagents.agents.web_security import WebSecurityAgent

async def test():
    agent = WebSecurityAgent()
    result = await agent.execute({'action': 'test'})
    print(result)

asyncio.run(test())
"
```

**Solution:**
```bash
# Increase timeout
export AGENT_TIMEOUT_SECONDS=600

# Restart specific agent
pkill -f "web_security"
python -m secagents.agents.web_security &

# Check for deadlocks
python -c "
import sys
import traceback
import threading

for thread_id, frame in sys._current_frames().items():
    print(f'Thread {thread_id}:')
    traceback.print_stack(frame)
"
```

### LLM API Errors
**Problem:** `AuthenticationError` or `APIError` from LLM provider

**Diagnosis:**
```bash
# Verify API key
echo $LLM_API_KEY

# Test API connection
curl -H "Authorization: Bearer $LLM_API_KEY" \
  https://api.openai.com/v1/models

# Check rate limits
grep -i "rate" logs/secagents-*.log | tail -20
```

**Solution:**
```bash
# Update API key
export LLM_API_KEY="new-key"

# Implement retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def call_llm(prompt):
    return llm.generate(prompt)

# Use fallback model
LLM_MODEL_PRIMARY="gpt-4"
LLM_MODEL_FALLBACK="gpt-3.5-turbo"
```

### Inconsistent Findings
**Problem:** Same endpoint returns different results on repeated scans

**Solution:**
```bash
# Enable deterministic mode
export SCAN_SEED=12345  # Use fixed seed

# Use canonical payloads
grep -r "PAYLOADS = " python-agents/secagents/modules/

# Add request deduplication
class RequestDeduplicator:
    def __init__(self):
        self.seen = set()
    
    def is_duplicate(self, request):
        key = (request.url, request.method, request.body)
        if key in self.seen:
            return True
        self.seen.add(key)
        return False
```

---

## Performance Issues

### Slow Scan Execution
**Problem:** Scans taking longer than expected

**Diagnosis:**
```bash
# Profile scan execution
python -m cProfile -s cumulative main.py

# Check resource utilization
top -p $(pgrep -f secagents)
docker stats secagents-api

# Identify slow agents
curl http://localhost:8000/metrics | jq '.agents[] | select(.avg_execution_time_ms > 1000)'
```

**Solution:**
```bash
# Increase concurrency
export MAX_CONCURRENT_SCANS=10
export WORKERS_PER_AGENT=4

# Scale horizontally
kubectl scale deployment secagents-api --replicas=5

# Optimize payloads
MAX_PAYLOADS_PER_CHECK=20  # Reduce from 50

# Use connection pooling
export POSTGRES_POOL_SIZE=20
export REDIS_MAX_CONNECTIONS=100

# Enable caching
@cache(ttl=3600)
def get_endpoints(target):
    return discover_endpoints(target)
```

### High Latency
**Problem:** API responses slow

**Diagnosis:**
```bash
# Check request latency
curl -w "Time: %{time_total}s\n" http://localhost:8000/health

# Monitor network
iftop -i eth0

# Check database query time
EXPLAIN ANALYZE SELECT * FROM findings WHERE severity = 'high';
```

**Solution:**
```bash
# Add database indexes
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_target ON findings(target);

# Use query caching
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;

# Implement response compression
gzip on;
gzip_types application/json;

# Use Redis caching
@cache_with_redis(ttl=300)
def get_agent_status():
    return compute_status()
```

### High Memory Usage
**Problem:** Container OOMKilled or memory pressure

**Diagnosis:**
```bash
# Check memory usage per process
ps aux --sort=-%mem | head -5

# Monitor heap size
python -c "
import tracemalloc
tracemalloc.start()
# ... run code ...
current, peak = tracemalloc.get_traced_memory()
print(f'Current: {current / 1024 / 1024:.1f}MB; Peak: {peak / 1024 / 1024:.1f}MB')
"

# Check for memory leaks
python -m objgraph show_most_common_types(limit=10)
```

**Solution:**
```bash
# Increase container memory limit
docker run -m 4g secagents:latest

# Tune Python garbage collection
export PYTHONGC_FREQUENCY=0
export PYTHONGC_THRESHOLD_OBJECTS=50000

# Reduce batch size
MAX_BATCH_SIZE=100  # Reduce from 500

# Stream results instead of buffering
async def stream_results():
    async for result in agent.scan_stream():
        yield result
```

---

## API Issues

### CORS Errors
**Problem:** `Cross-Origin Request Blocked`

**Solution:**
```python
# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 401 Unauthorized
**Problem:** `Authorization header invalid`

**Solution:**
```bash
# Verify API key format
curl -H "Authorization: Bearer your_key" http://localhost:8000/scans

# Check key expiration
redis-cli TTL "api_key:your_key"

# Generate new key
curl -X POST http://localhost:8000/auth/keys
```

### Rate Limiting
**Problem:** `429 Too Many Requests`

**Solution:**
```bash
# Wait before retrying
retry_after=$(curl -i http://localhost:8000/scans 2>/dev/null | grep Retry-After)

# Implement exponential backoff
for i in 1 2 4 8 16; do
    curl http://localhost:8000/scans && break || sleep $i
done

# Upgrade to higher rate limit tier
# Contact support for rate limit increase
```

---

## Debugging Tools

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("secagents").setLevel(logging.DEBUG)
```

### Interactive Debugger
```python
import pdb

async def execute_scan(target):
    pdb.set_trace()  # Debugger will pause here
    result = await scan_target(target)
    return result
```

### Remote Debugging
```python
# In production code
import debugpy
debugpy.listen(("0.0.0.0", 5678))
print("Debugger waiting...")

# Connect from IDE
# VS Code: Launch debugger pointing to 0.0.0.0:5678
```

### Health Check Script
```bash
#!/bin/bash

echo "=== SecAgents Health Check ==="

echo -n "API Status: "
curl -s http://localhost:8000/health | jq '.status' || echo "FAILED"

echo -n "PostgreSQL Status: "
psql -U postgres -c "SELECT 1" &>/dev/null && echo "OK" || echo "FAILED"

echo -n "Redis Status: "
redis-cli ping || echo "FAILED"

echo -n "Agents Status: "
curl -s http://localhost:8000/agents | jq '.overall_status' || echo "FAILED"

echo "=== End Health Check ==="
```

### Performance Profiling
```bash
# CPU profiling
python -m cProfile -s cumulative -o stats.prof main.py
python -c "import pstats; p = pstats.Stats('stats.prof'); p.print_stats(10)"

# Memory profiling
python -m memory_profiler main.py

# Flame graph
pip install py-spy
py-spy record -o profile.svg -- python main.py
```

---

## Getting Help

### Check Documentation
- API Documentation: `docs/API.md`
- Deployment Guide: `docs/DEPLOYMENT.md`
- Configuration: `docs/CONFIG.md`

### View Logs
```bash
# All logs
tail -f logs/*.log

# Structured logs (JSON)
cat logs/secagents-*.log | jq 'select(.level == "ERROR")'

# Filter by component
grep "web_security" logs/secagents-*.log
```

### Submit Issue
```bash
# Collect diagnostics
python -m secagents.scripts.diagnostics > diagnostics.json

# Submit with issue
curl -X POST https://github.com/secagents/issues \
  -d @diagnostics.json \
  -H "Authorization: Bearer $GITHUB_TOKEN"
```

