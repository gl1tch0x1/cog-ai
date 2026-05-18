"""OAST (Out-of-Band Application Security Testing) via Interactsh."""

from __future__ import annotations

import asyncio


class OASTClient:
    """Interactsh client for blind vulnerability detection."""

    def __init__(self, server: str = "oast.fun"):
        self.server = server
        self._session_id: str | None = None
        self._poll_url: str | None = None

    async def register(self) -> str:
        """Register and get a unique interaction URL."""
        # In production: full Interactsh protocol handshake
        import uuid
        self._session_id = uuid.uuid4().hex[:12]
        self._poll_url = f"https://{self._session_id}.{self.server}"
        return self._poll_url

    async def poll(self, timeout: int = 30) -> list[dict]:
        """Poll for out-of-band interactions."""
        if not self._session_id:
            return []
        interactions = []
        # In production: poll Interactsh API for DNS/HTTP callbacks
        await asyncio.sleep(min(timeout, 5))
        return interactions

    @property
    def callback_url(self) -> str | None:
        return self._poll_url


class BrowserCluster:
    """Headless browser pool for DOM-based testing."""

    def __init__(self, concurrency: int = 3, browser: str = "chromium"):
        self.concurrency = concurrency
        self.browser = browser
        self._sem = asyncio.Semaphore(concurrency)

    async def execute(self, url: str, script: str | None = None) -> dict:
        """Navigate to URL and optionally execute JS. Returns page data."""
        async with self._sem:
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    alerts: list[str] = []

                    async def handle_dialog(dialog):
                        alerts.append(dialog.message)
                        await dialog.dismiss()

                    page.on("dialog", handle_dialog)
                    await page.goto(url, timeout=15000)
                    if script:
                        await page.evaluate(script)
                    content = await page.content()
                    await browser.close()
                    return {"url": url, "alerts": alerts, "content_length": len(content)}
            except ImportError:
                return {"url": url, "error": "playwright not installed"}
            except Exception as e:
                return {"url": url, "error": str(e)}

    async def check_dom_xss(self, url: str, payload: str) -> bool:
        """Test if payload triggers alert in browser."""
        sep = "&" if "?" in url else "?"
        test_url = f"{url}{sep}q={payload}"
        result = await self.execute(test_url)
        return len(result.get("alerts", [])) > 0


class FeedbackLoop:
    """Persists confirmed/false-positive findings for learning."""

    def __init__(self, path: str = ".secagents/feedback.json"):
        import json
        from pathlib import Path
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = {"confirmed": [], "false_positives": []}
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text())
            except (json.JSONDecodeError, ValueError, OSError):
                self._data = {"confirmed": [], "false_positives": []}

    def confirm(self, finding_fingerprint: str) -> None:
        if finding_fingerprint not in self._data["confirmed"]:
            self._data["confirmed"].append(finding_fingerprint)
            self._save()

    def mark_false_positive(self, finding_fingerprint: str) -> None:
        if finding_fingerprint not in self._data["false_positives"]:
            self._data["false_positives"].append(finding_fingerprint)
            self._save()

    def is_known_fp(self, fingerprint: str) -> bool:
        return fingerprint in self._data["false_positives"]

    def _save(self) -> None:
        import json
        self._path.write_text(json.dumps(self._data, indent=2))
