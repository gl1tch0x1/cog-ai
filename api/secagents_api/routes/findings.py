"""Findings endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from secagents_api.database import get_db
from secagents_api.models import Finding, User
from secagents_api.auth import get_current_user
from secagents_api.schemas import FindingResponse, Severity

router = APIRouter()


@router.get("", response_model=List[FindingResponse])
async def list_findings(
    severity: Optional[Severity] = None,
    validated: Optional[bool] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Finding)
    if severity:
        query = query.where(Finding.severity == severity.value)
    if validated is not None:
        query = query.where(Finding.validated == validated)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found")
    return finding
