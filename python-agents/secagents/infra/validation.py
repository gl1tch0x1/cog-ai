"""Input validation and output sanitization."""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urlparse

SHELL_INJECTION_PATTERNS = re.compile(r"[;&|`$\n]|\$\(|&&|\|\|")
DANGEROUS_COMMANDS = {"docker", "kubectl", "mount", "dd", "chmod", "rm -rf", "mkfs"}


class InputValidator:
    @staticmethod
    def validate_path(path: str, base_dir: str = ".") -> tuple[bool, str]:
        try:
            resolved = Path(path).resolve()
            base = Path(base_dir).resolve()
            if not str(resolved).startswith(str(base)):
                return False, "Path traversal detected"
            return True, str(resolved)
        except Exception as e:
            return False, str(e)

    @staticmethod
    def validate_url(url: str) -> tuple[bool, str]:
        if len(url) > 2048:
            return False, "URL too long"
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Invalid scheme: {parsed.scheme}"
        if not parsed.netloc:
            return False, "Missing host"
        return True, url

    @staticmethod
    def validate_command(cmd: str) -> tuple[bool, str]:
        if SHELL_INJECTION_PATTERNS.search(cmd):
            return False, "Shell injection characters detected"
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in cmd.lower():
                return False, f"Dangerous command: {dangerous}"
        return True, cmd

    @staticmethod
    def validate_domain(domain: str) -> tuple[bool, str]:
        pattern = re.compile(r"^(?:\*\.)?[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z]{2,})+$")
        if pattern.match(domain):
            return True, domain
        return False, "Invalid domain format"


class OutputSanitizer:
    @staticmethod
    def sanitize_html(text: str) -> str:
        return html.escape(text)

    @staticmethod
    def sanitize_for_shell(text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9._\-/: ]", "", text)

    @staticmethod
    def sanitize_report(text: str, max_len: int = 100_000) -> str:
        text = text.replace("\x00", "")
        return text[:max_len]
