# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in SecAgents, please **DO NOT** open a public GitHub issue. Instead, email us at:

**security@secagents.io**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge your report within 48 hours and provide an update on our progress.

---

## Supported Versions

| Version | Status | Support Until | Security Updates |
|---------|--------|----------------|------------------|
| 0.2.x | ✅ Active | 2026-12-31 | ✅ Yes |
| 0.1.x | ⚠️ Legacy | 2026-08-31 | ⚠️ Critical Only |
| < 0.1.0 | ❌ Unsupported | - | ❌ No |

---

## Security Scope

We take security seriously for:

### ✅ In Scope
- Core AI Gateway and Orchestrator
- API and Database layers
- Agent execution contexts
- CLI tool and installer
- Authentication & authorization
- Input validation
- Cryptographic implementations
- Dependency vulnerabilities

### ⚠️ Out of Scope
- Social engineering
- Physical security
- Denial of Service (DoS) attacks
- Vulnerabilities in dependencies (report to vendor)
- Configuration errors by users

---

## Security Considerations

### ⚠️ Authorization & Scope

**SecAgents is designed ONLY for authorized security testing.**

- ✅ **Use on your own systems**
- ✅ **Use with explicit written permission**
- ✅ **Use in controlled lab environments**
- ✅ **Use for approved security assessments**

❌ **DO NOT use against systems you don't own or have permission to test**

### 🔐 Secrets Management

**Never commit secrets to the repository!**

- Use `.env` files (add to `.gitignore`)
- Use GitHub Secrets for CI/CD
- Rotate API keys regularly
- Use environment variables for sensitive data

### 🛡️ Secure Configuration

1. **Change default credentials**
   ```bash
   # Do NOT use default passwords in production
   POSTGRES_PASSWORD=changeme  # ❌ CHANGE THIS
   JWT_SECRET=your-secret-key
   ADMIN_PASSWORD=generate-strong-password
   ```

2. **Enable authentication**
   ```bash
   AUTH_ENABLED=true
   REQUIRE_MFA=false  # Enable in production
   ```

3. **Use HTTPS**
   ```bash
   # Enable SSL/TLS in production
   SSL_ENABLED=true
   SSL_CERT=/path/to/cert.pem
   SSL_KEY=/path/to/key.pem
   ```

4. **Set up firewall rules**
   ```bash
   # Restrict API access to authorized IPs only
   # Use VPN or private networks
   # Enable rate limiting
   ```

5. **Keep dependencies updated**
   ```bash
   pip install --upgrade pip
   pip install -U -r requirements.txt
   ```

### 🚨 Vulnerability Scanning

We use automated tools to scan for vulnerabilities:

- **Trivy** — Container and dependency scanning
- **Bandit** — Python security linting
- **Cargo Audit** — Rust dependency auditing
- **Dependabot** — Automated dependency updates

Every commit is scanned before merging.

---

## Incident Response

If a security issue is discovered:

1. **We will create a patch** within 7 days
2. **We will release a security update** (v0.2.1, etc.)
3. **We will publish a security advisory** with mitigation steps
4. **We will credit the reporter** (unless they request anonymity)

### Severity Levels

| Level | Response | Example |
|-------|----------|---------|
| **Critical** | 24-72 hours | RCE, authentication bypass |
| **High** | 3-7 days | SQL injection, privilege escalation |
| **Medium** | 1-2 weeks | Information disclosure, CSRF |
| **Low** | 2-4 weeks | XSS, weak headers |

---

## Security Features

### API Security

- ✅ CORS validation
- ✅ Rate limiting (100 req/min per IP)
- ✅ Input validation & sanitization
- ✅ SQL injection prevention (parameterized queries)
- ✅ CSRF token validation
- ✅ JWT token validation & expiration
- ✅ Secure password hashing (bcrypt with salt)
- ✅ Request signing for sensitive operations

### Infrastructure Security

- ✅ Docker security scanning
- ✅ Minimal base images (alpine)
- ✅ No root processes
- ✅ Read-only filesystems where possible
- ✅ Resource limits enforced
- ✅ Network policies enforced
- ✅ Secrets encrypted at rest
- ✅ Network segmentation

### Authentication & Authorization

- ✅ Multi-factor authentication support
- ✅ Role-based access control (RBAC)
- ✅ API key management
- ✅ OAuth 2.0 support
- ✅ Session timeout enforcement
- ✅ Audit logging of all access

---

## Compliance

SecAgents is built with security best practices:

- ✅ **OWASP Top 10** — Addresses known web vulnerabilities
- ✅ **CWE Coverage** — Covers 31+ CWE categories
- ✅ **Zero Trust Model** — Validates all inputs
- ✅ **Principle of Least Privilege** — Minimal permissions
- ✅ **Defense in Depth** — Multiple security layers
- ✅ **Secure Defaults** — Safe configurations out of the box

---

## Responsible Disclosure

If you find a vulnerability:

1. **Report privately** to security@secagents.io
2. **Include proof of concept** (if safe to do so)
3. **Allow 90 days** for our response before public disclosure
4. **Work with us** on a coordinated release

### What Happens After You Report

1. **Day 1** — We acknowledge receipt
2. **Day 3-5** — We confirm or dismiss the issue
3. **Day 7** — If confirmed, we create a fix
4. **Day 30** — We release a patch version
5. **Day 90** — Public disclosure of the issue

We appreciate responsible disclosure and will publicly credit security researchers who follow this process.

---

## Dependency Security

### Regular Audits

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Rust dependencies
cargo audit

# Go dependencies
go list -u -m all
```

### Updating Dependencies

```bash
# Python
pip install --upgrade pip setuptools wheel
pip install -U -r requirements.txt

# Rust
cargo update
cargo audit fix

# Go
go get -u ./...
go mod tidy
```

---

## Questions?

- 📖 **Documentation**: [docs/](docs/)
- 📧 **Email**: security@secagents.io
- 🐛 **GitHub Issues**: For non-security issues
- 💬 **Discussions**: For security best practices
