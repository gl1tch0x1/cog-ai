"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    OPTIMIZATION = "optimization"


class ScannerType(str, Enum):
    SAST = "sast"
    DAST = "dast"
    SCA = "sca"
    SECRET = "secret"
    AI_SECURITY = "ai_security"
    INFRA = "infra"


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# --- Targets ---
class TargetCreate(BaseModel):
    project_id: UUID
    domain: str
    scope: List[str] = []
    excluded: List[str] = []
    tags: List[str] = []


class TargetResponse(BaseModel):
    id: UUID
    project_id: UUID
    domain: str
    scope: List[str]
    excluded: List[str]
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Workflows ---
class WorkflowStart(BaseModel):
    target_id: UUID
    workflow_type: str = "bug_bounty"
    config: dict = {}


class WorkflowResponse(BaseModel):
    id: UUID
    target_id: UUID
    workflow_type: str
    status: str
    current_phase: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Findings ---
class FindingResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    target_id: UUID
    title: str
    severity: Severity
    scanner_type: ScannerType = ScannerType.SAST
    scanner_name: str
    cwe: Optional[str] = None
    cvss: Optional[float] = None
    summary: str
    steps: str
    impact: str
    remediation: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    validated: bool = False
    metadata: dict = {}
    created_at: datetime

    class Config:
        from_attributes = True


# --- Reports ---
class ReportResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    format: str
    finding_count: int
    created_at: datetime
    file_path: Optional[str] = None

    class Config:
        from_attributes = True

# --- Auth ---
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
