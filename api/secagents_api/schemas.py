"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import re as _re


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    OPTIMIZATION = "optimization"


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# --- Targets ---
_DOMAIN_RE = _re.compile(r"^(?!\-)([a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$")


class TargetCreate(BaseModel):
    project_id: UUID
    domain: str
    scope: List[str] = []
    excluded: List[str] = []
    tags: List[str] = []

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower().rstrip("/")
        # Strip protocol if provided
        if "://" in v:
            v = v.split("://", 1)[1].split("/")[0]
        # Strip port
        v = v.split(":")[0]
        if not _DOMAIN_RE.match(v):
            raise ValueError(
                "Invalid domain. Must be a valid hostname (e.g. example.com)"
            )
        if len(v) > 253:
            raise ValueError("Domain too long (max 253 characters)")
        return v


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
    cwe: Optional[str] = None
    cvss: Optional[float] = None
    summary: str
    steps: str
    impact: str
    remediation: str
    validated: bool = False
    false_positive: bool = False
    metadata: dict = Field(default={}, alias="metadata_")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


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
_EMAIL_RE = _re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password too long (max 128 characters)")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str
