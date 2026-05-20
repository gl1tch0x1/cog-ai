"""SecAgents API - FastAPI control plane."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from secagents_api.routes import targets, workflows, findings, reports, auth, dashboard

app = FastAPI(
    title="SecAgents API",
    version="0.2.0",
    description="Control-plane API for SecAgents cybersecurity platform",
)

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


@app.get("/health")
async def health():
    return {
        "status": "operational",
        "version": "0.2.0",
        "components": {
            "api": "ok",
            "worker": "requires secagents.worker process",
        },
    }
