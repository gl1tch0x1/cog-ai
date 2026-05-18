FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY secagents_api ./secagents_api
COPY migrations ./migrations
EXPOSE 8000
CMD ["uvicorn", "secagents_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
