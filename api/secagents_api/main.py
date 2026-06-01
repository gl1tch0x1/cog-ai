"""SecAgents API - FastAPI control plane."""

import os
import sys
import time

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from loguru import logger
from sqlalchemy import text
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from secagents_api.routes import targets, workflows, findings, reports, auth, dashboard
from secagents_api.database import engine

# Configure Loguru
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "pretty")

logger.remove()  # Remove default handler
if LOG_FORMAT == "json":
    logger.add(sys.stdout, level=LOG_LEVEL, serialize=True)
else:
    # High-fidelity offensive security palette
    fmt = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <white>{message}</white>"
    logger.add(sys.stdout, level=LOG_LEVEL, format=fmt, colorize=True)

# Configure OpenTelemetry
trace.set_tracer_provider(TracerProvider())
if os.environ.get("ENABLE_TRACING") == "true":
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(ConsoleSpanExporter())
    )

app = FastAPI(
    title="SecAgents API",
    version="0.3.0-dev",
    description="Control-plane API for SecAgents cybersecurity platform",
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "type": exc.__class__.__name__},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000

    logger.info(
        f"{request.method} {request.url.path} | Status: {response.status_code} | Latency: {round(process_time, 2)}ms",
    )
    return response


# CORS — allow frontend origins
_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(targets.router, prefix="/targets", tags=["targets"])
app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
app.include_router(findings.router, prefix="/findings", tags=["findings"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"

    return {
        "status": "operational" if db_status == "ok" else "degraded",
        "version": "0.3.0-dev",
        "components": {
            "api": "ok",
            "database": db_status,
            "worker": "requires secagents.worker process",
        },
    }
