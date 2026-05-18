# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Completed Authentication and Registration API routes (`/auth/register`, `/auth/token`).
- Implemented JWT validation via `oauth2_scheme` and `get_current_user`.
- Missing CVE verification payloads added for RFI, XXE, JWT None, CSRF, Cache Poisoning, AI Prompt Injection, OAuth Redirect, and IDOR.
- Added `asyncio` usage for retry delays in `BaseAgent` to prevent event loop blocking.

### Fixed
- Fixed IDE import errors for `Field` in `base.py`.
- Fixed missing CVE checks payload generator arrays rendering high severity bugs as header-only checks.
- Rewrote the main API endpoints to properly reflect SQLAlchemy asynchronous ORM usage.
