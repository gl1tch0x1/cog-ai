FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy configuration and source code
COPY pyproject.toml .
COPY secagents_api ./secagents_api
COPY migrations ./migrations

# Install the package and its dependencies
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "secagents_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
