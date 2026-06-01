# SecAgents Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Production Configuration](#production-configuration)
6. [Scaling](#scaling)
7. [Monitoring](#monitoring)

---

## Prerequisites

### System Requirements
- **CPU:** 4+ cores recommended
- **Memory:** 8GB+ RAM recommended
- **Storage:** 50GB+ for logs and findings
- **OS:** Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2

### Software Requirements
- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (for containerized deployment)
- kubectl (for Kubernetes deployment)

---

## Local Development

### 1. Clone Repository
```bash
git clone https://github.com/secagents/secagents.git
cd secagents
```

### 2. Set Up Python Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

**.env template:**
```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/secagents
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs/

# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Scanning
MAX_CONCURRENT_SCANS=5
SCAN_TIMEOUT_SECONDS=3600
```

### 4. Initialize Database
```bash
# Create database
createdb secagents

# Run migrations
python -m alembic upgrade head

# Seed initial data (optional)
python -m secagents.scripts.seed_db
```

### 5. Start Redis
```bash
redis-server
```

### 6. Start Services
```bash
# Terminal 1: API Server
python -m secagents.api.main

# Terminal 2: Orchestrator/Workers
python -m secagents.core.orchestrator

# Terminal 3: Frontend (if developing)
cd frontend/apex && npm start
```

### 7. Verify Installation
```bash
# Test API
curl http://localhost:8000/health

# Check agents
curl http://localhost:8000/agents
```

---

## Docker Deployment

### 1. Build Docker Image
```bash
docker build -t secagents:latest .
```

### 2. Docker Compose (Recommended)
```bash
docker-compose up -d
```

**docker-compose.yml reference:**
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: secagents
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/secagents
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend/apex
    ports:
      - "3000:3000"
    depends_on:
      - api
```

### 3. Run Individual Container
```bash
docker run -d \
  --name secagents-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/secagents \
  -e REDIS_URL=redis://host:6379/0 \
  secagents:latest
```

---

## Kubernetes Deployment

### 1. Create Namespace
```bash
kubectl create namespace secagents
```

### 2. Create ConfigMap
```bash
kubectl create configmap secagents-config \
  --from-file=.env \
  -n secagents
```

### 3. Create Secrets
```bash
kubectl create secret generic secagents-secrets \
  --from-literal=database-password=your-password \
  --from-literal=llm-api-key=your-key \
  -n secagents
```

### 4. Deploy StatefulSet for PostgreSQL
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: secagents
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: secagents
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: secagents-secrets
              key: database-password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi
```

### 5. Deploy API Service
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secagents-api
  namespace: secagents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: secagents-api
  template:
    metadata:
      labels:
        app: secagents-api
    spec:
      containers:
      - name: api
        image: secagents:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: postgresql://postgres:5432/secagents
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: secagents-secrets
              key: database-password
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: secagents-secrets
              key: llm-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### 6. Create Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: secagents-api
  namespace: secagents
spec:
  type: LoadBalancer
  selector:
    app: secagents-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

### 7. Deploy
```bash
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f service.yaml

# Verify
kubectl get pods -n secagents
kubectl logs -n secagents -f deployment/secagents-api
```

---

## Production Configuration

### 1. Environment Variables
```bash
# Set these in your production environment
export DATABASE_URL="postgresql://prod_user:strong_password@prod-db.example.com:5432/secagents"
export REDIS_URL="redis://:password@prod-redis.example.com:6379/0"
export API_DEBUG=false
export LOG_LEVEL=WARNING
export SECRET_KEY="generate-with-secrets-manager"
export ALLOWED_HOSTS="api.example.com,api2.example.com"
export CORS_ORIGINS="https://app.example.com"
```

### 2. Database Configuration
```bash
# Create production database with proper backups
createdb secagents_prod

# Enable WAL archiving for backups
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 3;
ALTER SYSTEM SET max_replication_slots = 3;
```

### 3. TLS/SSL Configuration
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
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Monitoring & Logging
```bash
# Set up ELK Stack or similar
# Configure log shipping
export SYSLOG_HOST="logs.example.com"
export SYSLOG_PORT="514"

# Enable Prometheus metrics
export METRICS_PORT="9090"
```

---

## Scaling

### Horizontal Scaling
```bash
# Scale API replicas
kubectl scale deployment secagents-api --replicas=5 -n secagents

# Scale workers
kubectl scale deployment secagents-workers --replicas=10 -n secagents
```

### Load Balancing
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: secagents-hpa
  namespace: secagents
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: secagents-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Monitoring

### Health Checks
```bash
# API health
curl https://api.example.com/health

# Agent status
curl https://api.example.com/agents

# Metrics
curl https://api.example.com/metrics
```

### Logging
```bash
# View logs
docker logs -f secagents-api

# Stream logs
kubectl logs -f deployment/secagents-api -n secagents

# View structured logs
tail -f logs/secagents-$(date +%Y%m%d).log | jq .
```

### Database Monitoring
```sql
-- Check connection count
SELECT count(*) FROM pg_stat_activity;

-- Monitor slow queries
SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Verify credentials
psql -h localhost -U secagents -d secagents -c "SELECT 1;"

# Check connection pool
SHOW max_connections;
```

#### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping

# Monitor connections
redis-cli CLIENT LIST

# Check memory
redis-cli INFO memory
```

#### High Memory Usage
```bash
# Scale horizontally
kubectl scale deployment secagents-api --replicas=5

# Tune Python GC
export PYTHONGC_DEBUG=1
```

#### Slow Scans
```bash
# Monitor orchestrator
curl http://localhost:8000/metrics | grep scan_duration

# Check agent performance
curl http://localhost:8000/agents | jq '.agents[].avg_execution_time_ms'
```

---

## Backup & Recovery

### Database Backup
```bash
# Full backup
pg_dump secagents > secagents_$(date +%Y%m%d).sql

# Restore
psql secagents < secagents_20240101.sql

# Automated backup
0 2 * * * pg_dump secagents | gzip > /backups/secagents_$(date +\%Y\%m\%d).sql.gz
```

### Restore from Backup
```bash
gunzip < /backups/secagents_20240101.sql.gz | psql secagents
```

