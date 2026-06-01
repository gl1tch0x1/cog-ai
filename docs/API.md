# SecAgents API Documentation

## Overview

SecAgents provides a REST API for programmatic access to vulnerability scanning and reporting capabilities. All endpoints return JSON responses and support standard HTTP methods.

---

## Base URL

```
https://api.secagents.io/v1
```

## Authentication

All requests require an API key in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

---

## Endpoints

### Scan Management

#### Create Scan
```
POST /scans
```

**Request:**
```json
{
  "target": "example.com",
  "scope": ".example.com",
  "scan_type": "full",
  "modules": ["recon", "web", "api"],
  "options": {
    "timeout": 3600,
    "max_concurrent": 10
  }
}
```

**Response:**
```json
{
  "id": "scan_20240101_001",
  "status": "queued",
  "created_at": "2024-01-01T00:00:00Z",
  "target": "example.com"
}
```

---

#### Get Scan Status
```
GET /scans/{scan_id}
```

**Response:**
```json
{
  "id": "scan_20240101_001",
  "status": "running",
  "progress": 45,
  "started_at": "2024-01-01T00:01:00Z",
  "estimated_completion": "2024-01-01T00:30:00Z",
  "current_phase": "web_security"
}
```

---

#### List Scans
```
GET /scans?status=completed&limit=10&offset=0
```

**Response:**
```json
{
  "scans": [
    {
      "id": "scan_20240101_001",
      "target": "example.com",
      "status": "completed",
      "findings_count": 15,
      "completed_at": "2024-01-01T00:30:00Z"
    }
  ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

---

#### Cancel Scan
```
DELETE /scans/{scan_id}
```

**Response:**
```json
{
  "id": "scan_20240101_001",
  "status": "cancelled",
  "cancelled_at": "2024-01-01T00:15:00Z"
}
```

---

### Findings

#### Get Findings
```
GET /scans/{scan_id}/findings?severity=high&type=xss
```

**Response:**
```json
{
  "findings": [
    {
      "id": "finding_001",
      "type": "xss",
      "severity": "high",
      "cvss": 7.5,
      "cwe": "CWE-79",
      "endpoint": "/search",
      "parameter": "q",
      "poc_url": "https://example.com/search?q=<img+src=x+onerror=alert(1)>",
      "proof_signal": "<img src=x onerror=alert(1)>",
      "impact": "Attacker can execute arbitrary JavaScript",
      "remediation": "Implement output encoding",
      "verified": true,
      "discovered_at": "2024-01-01T00:05:00Z"
    }
  ],
  "total": 15
}
```

---

#### Get Finding Detail
```
GET /scans/{scan_id}/findings/{finding_id}
```

**Response:**
```json
{
  "id": "finding_001",
  "type": "xss",
  "severity": "high",
  "cvss": 7.5,
  "cve": "CVE-2024-0001",
  "cwe": "CWE-79",
  "endpoint": "/search",
  "parameter": "q",
  "method": "GET",
  "poc_request": {
    "url": "https://example.com/search?q=<img+src=x+onerror=alert(1)>",
    "headers": {}
  },
  "poc_response": {
    "status": 200,
    "body": "<html><img src=x onerror=alert(1)></html>"
  },
  "proof_signal": "<img src=x onerror=alert(1)>",
  "impact": "Attacker can execute arbitrary JavaScript in victim's browser",
  "remediation": "Implement HTML entity encoding on user input",
  "remediation_priority": "high",
  "tags": ["xss", "reflected", "user-input"],
  "evidence": [
    {
      "type": "request",
      "data": "GET /search?q=<img+src=x+onerror=alert(1)>"
    },
    {
      "type": "response",
      "data": "<html><img src=x onerror=alert(1)></html>"
    }
  ]
}
```

---

#### Validate Finding
```
POST /scans/{scan_id}/findings/{finding_id}/validate
```

**Request:**
```json
{
  "revalidate": true
}
```

**Response:**
```json
{
  "id": "finding_001",
  "status": "verified",
  "still_vulnerable": true,
  "validation_time": "2024-01-01T00:20:00Z",
  "new_evidence": []
}
```

---

### Reports

#### Generate Report
```
POST /scans/{scan_id}/report
```

**Request:**
```json
{
  "format": "pdf",
  "include_findings": true,
  "include_methodology": true,
  "include_remediation": true
}
```

**Response:**
```json
{
  "report_id": "report_001",
  "status": "generating",
  "format": "pdf",
  "download_url": "https://api.secagents.io/reports/report_001/download"
}
```

---

#### List Reports
```
GET /scans/{scan_id}/reports
```

**Response:**
```json
{
  "reports": [
    {
      "id": "report_001",
      "format": "pdf",
      "status": "ready",
      "created_at": "2024-01-01T00:30:00Z",
      "download_url": "https://api.secagents.io/reports/report_001/download"
    }
  ]
}
```

---

### Agent Status

#### Get Agent Status
```
GET /agents/{agent_name}
```

**Response:**
```json
{
  "name": "web_security",
  "status": "healthy",
  "uptime_seconds": 86400,
  "tasks_completed": 1250,
  "tasks_failed": 3,
  "avg_execution_time_ms": 1450
}
```

---

#### Get All Agents Status
```
GET /agents
```

**Response:**
```json
{
  "agents": [
    {
      "name": "supervisor",
      "status": "healthy",
      "uptime_seconds": 86400
    },
    {
      "name": "planner",
      "status": "healthy",
      "uptime_seconds": 86400
    },
    {
      "name": "recon",
      "status": "healthy",
      "uptime_seconds": 86400
    }
  ],
  "overall_status": "healthy"
}
```

---

### Health & System

#### System Health
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "api": "healthy",
    "database": "healthy",
    "redis": "healthy",
    "orchestrator": "healthy"
  },
  "version": "0.2.0"
}
```

---

#### System Metrics
```
GET /metrics
```

**Response:**
```json
{
  "uptime_seconds": 86400,
  "total_scans": 542,
  "active_scans": 12,
  "total_findings": 8734,
  "avg_scan_duration_seconds": 450,
  "memory_usage_mb": 1024,
  "cpu_usage_percent": 35
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request parameters |
| AUTH_ERROR | 401 | Missing or invalid authentication |
| AUTHZ_ERROR | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| TIMEOUT_ERROR | 408 | Request timeout |
| CONFLICT | 409 | Resource conflict (duplicate, etc) |
| RATE_LIMIT | 429 | Rate limit exceeded |
| SERVER_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

---

## Rate Limiting

Rate limits:
- 100 requests/minute for authenticated requests
- 10 requests/minute for unauthenticated requests

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

---

## Examples

### Python
```python
import requests

api_key = "your_api_key"
headers = {"Authorization": f"Bearer {api_key}"}

# Create scan
response = requests.post(
    "https://api.secagents.io/v1/scans",
    json={
        "target": "example.com",
        "scan_type": "full"
    },
    headers=headers
)

scan_id = response.json()["id"]

# Get findings
response = requests.get(
    f"https://api.secagents.io/v1/scans/{scan_id}/findings",
    headers=headers
)

findings = response.json()["findings"]
```

### cURL
```bash
# Create scan
curl -X POST https://api.secagents.io/v1/scans \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "scan_type": "full"
  }'

# Get findings
curl https://api.secagents.io/v1/scans/scan_id/findings \
  -H "Authorization: Bearer your_api_key"
```

---

## Webhooks

SecAgents supports webhooks for asynchronous notifications:

```
POST /webhook-configs
```

**Request:**
```json
{
  "url": "https://your-domain.com/webhook",
  "events": ["scan.completed", "finding.discovered"],
  "secret": "webhook_secret"
}
```

**Webhook Payload:**
```json
{
  "event": "finding.discovered",
  "timestamp": "2024-01-01T00:00:00Z",
  "scan_id": "scan_001",
  "data": {
    "finding_id": "finding_001",
    "type": "xss",
    "severity": "high"
  }
}
```

---

## Changelog

### v1.0
- Initial API release
- Scan management endpoints
- Finding retrieval and validation
- Report generation
- Agent status monitoring
- Webhook support

