# SecAgents Configuration Reference

## Environment Variables

### Core API Configuration
```bash
# API Server
API_HOST=0.0.0.0                           # Bind address
API_PORT=8000                              # Port
API_DEBUG=false                            # Debug mode
SECRET_KEY=your-secret-key                 # Session secret (generate: openssl rand -hex 32)
ALLOWED_HOSTS=localhost,127.0.0.1          # Comma-separated allowed hosts

# CORS
CORS_ORIGINS=http://localhost:3000         # Frontend origin
CORS_CREDENTIALS=true                      # Allow credentials
CORS_METHODS=GET,POST,PUT,DELETE           # Allowed HTTP methods
CORS_HEADERS=*                             # Allowed headers
```

### Database Configuration
```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/secagents
DATABASE_POOL_SIZE=20                      # Connection pool size
DATABASE_ECHO=false                        # Log all SQL queries
DATABASE_TIMEOUT=30                        # Connection timeout (seconds)
DATABASE_SSL=false                         # Use SSL connection

# Migrations
ALEMBIC_SQLALCHEMY_URL=$DATABASE_URL       # Alembic migration URL
```

### Redis Configuration
```bash
# Redis Cache
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=20                         # Connection pool size
REDIS_SOCKET_TIMEOUT=5                     # Socket timeout (seconds)
REDIS_SOCKET_CONNECT_TIMEOUT=5             # Connection timeout (seconds)
REDIS_RETRY_ON_TIMEOUT=true                # Retry on timeout
REDIS_DB=0                                 # Database number
```

### LLM Provider Configuration

#### OpenAI
```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-...                         # Your OpenAI API key
LLM_MODEL=gpt-4-turbo-preview              # Model to use
LLM_TEMPERATURE=0.1                        # Temperature (0-2)
LLM_MAX_TOKENS=2000                        # Max tokens per response
LLM_TIMEOUT=30                             # Request timeout (seconds)
LLM_RETRY_COUNT=3                          # Retry attempts
```

#### Anthropic (Claude)
```bash
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...                     # Your Anthropic API key
LLM_MODEL=claude-3-sonnet-20240229         # Model to use
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000
```

#### Azure OpenAI
```bash
LLM_PROVIDER=azure
LLM_API_KEY=...                            # Your Azure API key
LLM_ENDPOINT=https://your-resource.openai.azure.com/
LLM_DEPLOYMENT=gpt-4-deployment            # Deployment name
LLM_API_VERSION=2024-02-01                 # API version
```

#### Local (Ollama)
```bash
LLM_PROVIDER=ollama
LLM_ENDPOINT=http://localhost:11434        # Ollama endpoint
LLM_MODEL=llama2                           # Local model name
```

### Scanning Configuration
```bash
# Scan Execution
MAX_CONCURRENT_SCANS=5                     # Maximum concurrent scans
SCAN_TIMEOUT_SECONDS=3600                  # Scan timeout (1 hour)
WORKERS_PER_AGENT=2                        # Workers per agent
TASK_QUEUE_MAX_SIZE=1000                   # Max queued tasks
TASK_RETRY_COUNT=3                         # Task retry attempts
TASK_RETRY_BACKOFF=2                       # Exponential backoff factor

# Payload Configuration
MAX_PAYLOADS_PER_CHECK=50                  # Payloads per vulnerability check
PAYLOAD_TIMEOUT=10                         # Per-payload timeout (seconds)
PAYLOAD_CONCURRENT_LIMIT=5                 # Concurrent payloads
DETERMINISTIC_SEED=42                      # Seed for reproducible tests
```

### Logging Configuration
```bash
# Logging
LOG_LEVEL=INFO                             # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_DIR=logs                               # Log directory
LOG_FORMAT=json                            # Log format (json or text)
LOG_MAX_SIZE=100                           # Max log file size (MB)
LOG_BACKUP_COUNT=5                         # Number of backup files
SYSLOG_ENABLED=false                       # Enable syslog
SYSLOG_HOST=localhost                      # Syslog host
SYSLOG_PORT=514                            # Syslog port
```

### Security Configuration
```bash
# Security
REQUIRE_HTTPS=false                        # Require HTTPS (set true in production)
SSL_CERT_PATH=/etc/ssl/certs/server.crt   # SSL certificate path
SSL_KEY_PATH=/etc/ssl/private/server.key   # SSL key path
JWT_SECRET=$SECRET_KEY                     # JWT signing secret
JWT_EXPIRATION=3600                        # JWT expiration (seconds)
JWT_ALGORITHM=HS256                        # JWT algorithm

# Rate Limiting
RATE_LIMIT_ENABLED=true                    # Enable rate limiting
RATE_LIMIT_REQUESTS=100                    # Requests per period
RATE_LIMIT_PERIOD=60                       # Period in seconds
RATE_LIMIT_STORAGE=redis                   # Storage backend (redis or memory)

# API Key Management
API_KEY_LENGTH=32                          # Generated key length
API_KEY_EXPIRATION=0                       # 0 = never expire (seconds)
```

### Agent Configuration
```bash
# Agent Settings
AGENT_TIMEOUT=300                          # Agent execution timeout (seconds)
AGENT_RETRY_COUNT=2                        # Agent retry attempts
AGENT_LOG_LEVEL=INFO                       # Agent log level
AGENT_HEARTBEAT_INTERVAL=30                # Heartbeat interval (seconds)

# Specific Agents
RECON_AGENT_ENABLED=true
RECON_AGENT_WORKERS=2
RECON_MAX_SUBDOMAINS=1000

WEB_SECURITY_AGENT_ENABLED=true
WEB_SECURITY_AGENT_WORKERS=4
WEB_SECURITY_MAX_ENDPOINTS=500

API_SECURITY_AGENT_ENABLED=true
API_SECURITY_AGENT_WORKERS=2

VALIDATOR_AGENT_ENABLED=true
VALIDATOR_CONCURRENCY=10

REPORT_AGENT_ENABLED=true
```

### Storage Configuration
```bash
# File Storage
STORAGE_BACKEND=local                      # local, s3, or gcs
STORAGE_PATH=./data                        # Local storage path

# S3 Storage
S3_BUCKET=secagents-findings
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...

# GCS Storage
GCS_BUCKET=secagents-findings
GCS_PROJECT_ID=...
GCS_SERVICE_ACCOUNT_JSON=/path/to/key.json
```

### Notification Configuration
```bash
# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=noreply@secagents.io
SMTP_USE_TLS=true

# Webhook
WEBHOOK_ENABLED=true
WEBHOOK_SIGNATURE_SECRET=...               # For validating signatures
WEBHOOK_TIMEOUT=10                         # Webhook timeout (seconds)
WEBHOOK_RETRY_COUNT=3

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#security
```

### Observability Configuration
```bash
# Metrics
PROMETHEUS_ENABLED=true                    # Enable Prometheus metrics
PROMETHEUS_PORT=9090                       # Metrics port
METRICS_INCLUDE=[]                         # Specific metrics to include

# Tracing
TRACING_ENABLED=false                      # Distributed tracing
TRACING_BACKEND=jaeger                     # jaeger or zipkin
TRACING_SAMPLE_RATE=0.1                    # 10% sampling

# Health Checks
HEALTHCHECK_ENABLED=true
HEALTHCHECK_INTERVAL=30                    # Seconds
HEALTHCHECK_TIMEOUT=5                      # Seconds
```

### Advanced Configuration
```bash
# Circuit Breaker
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5        # Failures before opening
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2        # Successes before closing
CIRCUIT_BREAKER_TIMEOUT=60                 # Timeout before half-open (seconds)

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=3600                             # Cache TTL (seconds)
CACHE_MAX_SIZE=1000                        # Max cached items

# Feature Flags
FEATURE_AUTOPILOT_MODE=true                # Enable autopilot
FEATURE_EXPLOIT_CHAINING=true              # Enable exploit chain correlation
FEATURE_AI_VALIDATION=true                 # Enable AI-based validation
```

---

## Configuration Files

### .env Template
```bash
# Copy this to .env and update with your values

# Core
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
SECRET_KEY=$(openssl rand -hex 32)

# Database
DATABASE_URL=postgresql://secagents:password@localhost:5432/secagents

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo-preview

# Scanning
MAX_CONCURRENT_SCANS=5
SCAN_TIMEOUT_SECONDS=3600

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs/
```

### config.yaml Example
```yaml
api:
  host: 0.0.0.0
  port: 8000
  debug: false
  secret_key: generated-secret

database:
  url: postgresql://user:password@localhost:5432/secagents
  pool_size: 20
  echo: false

redis:
  url: redis://localhost:6379/0
  pool_size: 20

llm:
  provider: openai
  api_key: ${LLM_API_KEY}
  model: gpt-4-turbo-preview
  temperature: 0.1

scanning:
  max_concurrent: 5
  timeout: 3600
  workers_per_agent: 2

logging:
  level: INFO
  format: json
  directory: logs/

agents:
  recon:
    enabled: true
    workers: 2
  web_security:
    enabled: true
    workers: 4
  api_security:
    enabled: true
    workers: 2
```

---

## Setting Configuration

### Method 1: Environment Variables
```bash
export API_PORT=8000
export DATABASE_URL="postgresql://..."
python -m secagents.api.main
```

### Method 2: .env File
```bash
# Create .env file
cp .env.example .env

# Edit .env with your values
source .env
python -m secagents.api.main
```

### Method 3: Configuration File
```python
from secagents.config import Config

config = Config.from_file("config.yaml")
app = create_app(config)
```

### Method 4: Programmatic
```python
from secagents.config import Config

config = Config(
    api_port=8000,
    database_url="postgresql://...",
    llm_provider="openai"
)
app = create_app(config)
```

---

## Validation

### Check Configuration
```bash
# Verify configuration
python -c "from secagents.config import Config; Config.validate()"

# Print loaded configuration
python -c "from secagents.config import Config; print(Config.to_dict())"

# Test connections
python -m secagents.scripts.test_config

# Generate sample config
python -m secagents.scripts.generate_config
```

---

## Production Checklist

- [ ] Set `API_DEBUG=false`
- [ ] Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- [ ] Set `REQUIRE_HTTPS=true`
- [ ] Configure SSL certificates
- [ ] Use environment-specific database
- [ ] Enable `RATE_LIMIT_ENABLED=true`
- [ ] Configure `LLM_API_KEY` securely (use secrets manager)
- [ ] Set `LOG_LEVEL=WARNING` (reduce log volume)
- [ ] Enable `PROMETHEUS_ENABLED=true`
- [ ] Configure backup strategy
- [ ] Test disaster recovery

