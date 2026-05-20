# SecAgent Fortress sandbox — isolated tool execution
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Security tools (subset; extend as needed)
RUN pip install --no-cache-dir httpx requests

# Non-root execution
RUN useradd -m -u 1000 secagent
USER secagent

ENTRYPOINT ["/bin/sh", "-c"]
