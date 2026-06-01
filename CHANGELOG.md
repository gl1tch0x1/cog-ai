# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] — 2026-05-20

### 🎯 Major Release: Production-Ready Infrastructure

#### ✨ Added

**Release & Deployment:**
- ✅ Fixed GitHub release workflow — releases now publish correctly to GitHub Releases
- ✅ Multi-platform binary builds (Linux, Windows, macOS)
- ✅ Automated Docker image publishing to GHCR
- ✅ PyPI package publishing pipeline
- ✅ Release validation and tag verification
- ✅ Comprehensive release notes generation
- ✅ SHA256 checksum generation for binary integrity

**CI/CD Pipeline:**
- ✅ Complete GitHub Actions CI workflow for all languages (Python, Rust, Go, JavaScript)
- ✅ Linting & formatting checks (ruff, rustfmt, gofmt, prettier)
- ✅ Type checking (mypy, TypeScript)
- ✅ Security scanning (Trivy, bandit)
- ✅ Test execution with coverage tracking
- ✅ Docker image building
- ✅ Integration tests for full system verification

**Documentation:**
- ✅ Quick Start Guide (`docs/QUICKSTART.md`)
- ✅ Release & Deployment Guide (`docs/RELEASES.md`)
- ✅ Version management system (`_version.py`)
- ✅ Comprehensive workflow documentation
- ✅ Troubleshooting guides

**Version Management:**
- ✅ Centralized version in `secagents._version`
- ✅ Semantic versioning support (X.Y.Z format)
- ✅ Pre-release support (alpha, beta, rc)
- ✅ Version verification in release workflow

#### 🐛 Fixed

**Release Issues:**
- 🔧 Fixed "No releases published" error by correcting artifact paths
- 🔧 Fixed workflow permissions (added `contents: write`)
- 🔧 Fixed tag validation regex
- 🔧 Fixed missing __main__.py for PyInstaller
- 🔧 Fixed artifact download paths in release job

**CI/CD Issues:**
- 🔧 Fixed Python test discovery paths
- 🔧 Fixed Rust compilation issues
- 🔧 Fixed Go module loading
- 🔧 Fixed frontend build configuration
- 🔧 Fixed service dependencies in tests

**Documentation:**
- 🔧 Fixed broken links in README
- 🔧 Fixed incomplete prerequisite list
- 🔧 Added missing installation instructions
- 🔧 Added missing configuration examples

#### 🚀 Improvements

- **Enhanced Release Workflow** — 9 parallel jobs for faster builds
- **Comprehensive Testing** — Tests run on Python/Rust/Go/JS in parallel
- **Security Scanning** — Automated vulnerability detection on every commit
- **Better Diagnostics** — Detailed logs and status checks
- **Production Ready** — Full validation before publishing releases

#### 📦 Dependencies (Unchanged)

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Rust 1.70+
- Go 1.21+
- Node.js 20+

#### 🔗 Artifacts

- **CLI Binaries**: `secagent-linux-x64`, `secagent-windows-x64.exe`, `secagent-macos-x64`
- **Docker Images**: `ghcr.io/secagents/{api,rust-core,recon}:0.2.0`
- **Python Packages**: `secagents==0.2.0`, `secagents-api==0.1.0`

---

## [0.1.0] — Initial Release

### 🎯 Core Features

#### ✨ Added

- Autonomous multi-agent security testing framework
- 7 specialized agent types (Supervisor, Planner, Recon, WebSec, APISec, Validator, Reporter)
- 31 deterministic CVE checks
- FastAPI REST control plane
- Next.js APEX dashboard
- PostgreSQL + Redis infrastructure
- Docker Compose deployment
- Multi-LLM provider support (OpenAI, Anthropic, Groq, DeepSeek, Gemini, Ollama, xAI)
- Go-based reconnaissance engine
- Rust workflow scheduler

#### 📝 Documentation

- Architecture documentation
- Security policy
- Contributing guidelines
- License (MIT)

---

## How to Upgrade

```bash
# From 0.1.0 to 0.2.0
git pull origin main
git checkout v0.2.0
docker compose down
docker compose pull
docker compose up -d
```

---

## Roadmap

### Planned for 0.3.0
- [ ] Machine learning false positive filtering
- [ ] Advanced exploit chaining
- [ ] Mobile app scanning
- [ ] GraphQL fuzzing
- [ ] Kubernetes security auditing

### Planned for 0.4.0
- [ ] Distributed agent network
- [ ] Cloud provider-specific checks
- [ ] Hardware security module (HSM) support
- [ ] Advanced threat intelligence integration
- [ ] Zero Trust security model assessment

---

## Support

For issues or questions:
- 🐛 **Report bugs**: [GitHub Issues](https://github.com/secagents/secagents/issues)
- 📖 **Documentation**: [docs/](docs/)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/secagents/secagents/discussions)
- 🛡️ **Security**: [SECURITY.md](SECURITY.md)
