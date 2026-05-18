FROM python:3.12-slim

# Install system dependencies + compilers for C and Rust extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    pkg-config \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install build tools explicitly
RUN pip install --no-cache-dir --upgrade pip setuptools wheel hatchling

# Copy metadata and source from the root context (context: .)
COPY api/pyproject.toml ./
# Satisfy hatchling/pip requirement for a README
RUN touch README.md

# Copy the package source BEFORE installation
COPY api/secagents_api ./secagents_api
COPY api/migrations ./migrations

# Install the package with verbose output for debugging
RUN pip install --no-cache-dir -v .

EXPOSE 8000
CMD ["uvicorn", "secagents_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
