"""Module 8: Auto-patch suggestions for common vulnerabilities."""

from __future__ import annotations


PATCH_TEMPLATES: dict[str, str] = {
    "sqli": """# Remediation: Use parameterized queries
# Before (vulnerable):
# cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
# After (secure):
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
""",
    "xss": """# Remediation: Encode output and use CSP
# Python/Flask: {{ user_input | e }}
# Set header: Content-Security-Policy: default-src 'self'
""",
    "ssrf": """# Remediation: Block private IPs and validate URLs
ALLOWED_SCHEMES = {'https'}
# Use urllib.parse and reject 127.0.0.0/8, 10.0.0.0/8, 169.254.0.0/16
""",
    "path_traversal": """# Remediation: Canonicalize paths
import os
safe = os.path.realpath(os.path.join(base_dir, user_path))
if not safe.startswith(base_dir):
    raise ValueError("Path traversal detected")
""",
    "command_injection": """# Remediation: Never pass user input to shell
# Use subprocess with list args, not shell=True
subprocess.run(["ping", "-c", "1", validated_host], shell=False)
""",
    "ssti": """# Remediation: Sandbox templates; avoid user-controlled templates
# Use Jinja2 SandboxedEnvironment
from jinja2.sandbox import SandboxedEnvironment
env = SandboxedEnvironment()
""",
    "xxe": """# Remediation: Disable external entities in XML parsers
# defusedxml or lxml with resolve_entities=False
""",
    "idor": """# Remediation: Enforce authorization on every object access
# if resource.owner_id != current_user.id: raise Forbidden
""",
}


class AutoPatcher:
    """Generate secure patch suggestions for validated findings."""

    def generate_patch(self, finding: dict) -> dict:
        vuln = finding.get("vuln_type", finding.get("type", "")).lower()
        template = PATCH_TEMPLATES.get(vuln, "# Review manually — no auto-patch template for this class")
        return {
            "vuln_type": vuln,
            "patch_snippet": template,
            "language": "python",
            "automated": vuln in PATCH_TEMPLATES,
        }

    def apply_to_findings(self, findings: list[dict]) -> list[dict]:
        for f in findings:
            if f.get("validated"):
                f["remediation_patch"] = self.generate_patch(f)
        return findings
