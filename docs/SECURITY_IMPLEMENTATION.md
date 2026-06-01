# SecAgents Security Implementation Guide

## Table of Contents
1. [Input Validation](#input-validation)
2. [Rate Limiting](#rate-limiting)
3. [Secrets Management](#secrets-management)
4. [CORS Configuration](#cors-configuration)
5. [Authentication & Authorization](#authentication--authorization)
6. [API Key Management](#api-key-management)

---

## Input Validation

### Endpoint-Level Validation
```python
from pydantic import BaseModel, Field, validator

class ScanRequest(BaseModel):
    """Validated scan request model."""
    
    target: str = Field(..., min_length=1, max_length=255)
    scope: str = Field(..., regex=r'^[\w\.\-*]+$')
    scan_type: str = Field(default="full", regex=r'^(full|quick|targeted)$')
    
    @validator('target')
    def validate_target(cls, v):
        """Validate target is valid domain or IP."""
        import re
        domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        
        if not (re.match(domain_pattern, v) or re.match(ip_pattern, v)):
            raise ValueError('Invalid target format')
        return v

# Automatic validation via FastAPI
@app.post("/v1/scans")
async def create_scan(request: ScanRequest):
    # Request is automatically validated
    return {"status": "success"}
```

### Payload Validation
```python
import re

class PayloadValidator:
    """Validate and sanitize payloads."""
    
    # Whitelist allowed characters
    SAFE_PATTERN = re.compile(r'^[\w\-\.\<\>\/\=\&\?\#\(\)\[\]\{\}]*$')
    
    # Blacklist dangerous patterns
    DANGEROUS_PATTERNS = [
        r'__import__',
        r'eval\(',
        r'exec\(',
        r'os\.system',
        r'subprocess',
    ]
    
    @staticmethod
    def validate(payload: str, max_length: int = 1000) -> bool:
        """Validate payload is safe."""
        
        # Check length
        if len(payload) > max_length:
            return False
        
        # Check against dangerous patterns
        for pattern in PayloadValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, payload, re.IGNORECASE):
                return False
        
        return True
```

---

## Rate Limiting

### Implementation
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/scans")
@limiter.limit("100/minute")
async def create_scan(request: Request, scan_data: ScanRequest):
    """Create scan with rate limiting."""
    return {"id": "scan_123"}

# Per-user rate limiting
@app.get("/v1/scans")
@limiter.limit("1000/hour", key_func=lambda r: r.headers.get("X-API-Key"))
async def list_scans(request: Request):
    """List scans with per-user rate limiting."""
    return []
```

### Rate Limit Headers
```python
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Add rate limit info to responses."""
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "95"
    response.headers["X-RateLimit-Reset"] = "1609459200"
    
    return response
```

---

## Secrets Management

### Environment Variables
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings from environment."""
    
    # API
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY not set")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")
    
    # LLM
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    if not LLM_API_KEY:
        raise ValueError("LLM_API_KEY not set")
```

### Secrets Vault Integration
```python
from hashicorp_vault import Client

class VaultSecrets:
    """Fetch secrets from HashiCorp Vault."""
    
    def __init__(self, vault_addr: str, vault_token: str):
        self.client = Client(url=vault_addr, token=vault_token)
    
    def get_secret(self, path: str) -> str:
        """Get secret from vault."""
        response = self.client.secrets.kv.read_secret_version(path=path)
        return response['data']['data']['value']

# Usage
vault = VaultSecrets(
    vault_addr="https://vault.example.com:8200",
    vault_token=os.getenv("VAULT_TOKEN")
)

DATABASE_PASSWORD = vault.get_secret("database/password")
```

---

## CORS Configuration

### Restrictive CORS
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.example.com",
        "https://app2.example.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,  # 10 minutes
)
```

### Dynamic CORS
```python
def is_trusted_origin(origin: str) -> bool:
    """Check if origin is trusted."""
    trusted_domains = [
        "app.example.com",
        "app2.example.com"
    ]
    
    for domain in trusted_domains:
        if origin.endswith(f".{domain}") or origin == f"https://{domain}":
            return True
    
    return False

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    """Dynamic CORS middleware."""
    origin = request.headers.get("origin")
    
    response = await call_next(request)
    
    if origin and is_trusted_origin(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response
```

---

## Authentication & Authorization

### JWT Authentication
```python
from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)
    
    return username

@app.get("/v1/scans")
async def list_scans(current_user: str = Depends(verify_token)):
    """List scans for authenticated user."""
    return []
```

### OAuth2 Integration
```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.get('/auth/login')
async def login(request: Request):
    """Initiate OAuth login."""
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth/callback')
async def auth_callback(request: Request):
    """OAuth callback."""
    token = await oauth.google.authorize_access_token(request)
    user = token.get('userinfo')
    
    # Store user session
    return {"status": "authenticated"}
```

---

## API Key Management

### Generate API Keys
```python
import secrets
from datetime import datetime, timedelta

class APIKeyManager:
    """Manage API keys."""
    
    @staticmethod
    def generate_key(length: int = 32) -> str:
        """Generate secure API key."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash API key for storage."""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()

# Database model
class APIKey(Base):
    """API key model."""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key_hash = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
```

### Validate API Keys
```python
async def validate_api_key(request: Request):
    """Validate API key from header."""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401)
    
    token = auth_header[7:]  # Remove "Bearer "
    
    # Hash and lookup in database
    token_hash = APIKeyManager.hash_key(token)
    key = await db.query(APIKey).filter(
        APIKey.key_hash == token_hash,
        APIKey.is_active == True
    ).first()
    
    if not key:
        raise HTTPException(status_code=401)
    
    if key.expires_at and key.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Key expired")
    
    # Update last used
    key.last_used_at = datetime.utcnow()
    await db.commit()
    
    return key.user_id

@app.get("/v1/scans")
async def list_scans(user_id: int = Depends(validate_api_key)):
    """List scans for user."""
    return []
```

---

## Security Checklist

### Development
- [ ] Run security linter: `bandit -r python-agents/`
- [ ] Check dependencies: `pip-audit`
- [ ] Run SAST: `semgrep --config p/security-audit`
- [ ] Check secrets: `git-secrets --scan`

### Testing
- [ ] Test input validation
- [ ] Test auth failure scenarios
- [ ] Test rate limiting
- [ ] Test CORS misconfiguration

### Deployment
- [ ] Use HTTPS only (`REQUIRE_HTTPS=true`)
- [ ] Configure SSL/TLS certificates
- [ ] Set secure headers
- [ ] Enable HSTS
- [ ] Use security.txt

### Runtime
- [ ] Monitor for suspicious patterns
- [ ] Log security events
- [ ] Alert on authentication failures
- [ ] Track API key usage

---

## Secure Headers

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to responses."""
    response = await call_next(request)
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # HSTS
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # CSP
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response
```

