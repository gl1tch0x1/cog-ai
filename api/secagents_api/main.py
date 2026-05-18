"""SecAgents API - FastAPI control plane."""

from fastapi import FastAPI
from secagents_api.routes import targets, workflows, findings, reports, auth

app = FastAPI(
    title="SecAgents API",
    version="0.1.0",
    description="Control-plane API for SecAgents cybersecurity platform",
)

app.include_router(targets.router, prefix="/targets", tags=["targets"])
app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
app.include_router(findings.router, prefix="/findings", tags=["findings"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health():
    return {"status": "ok"}
