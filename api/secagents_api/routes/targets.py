"""Target management endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from secagents_api.database import get_db
from secagents_api.models import Target, User
from secagents_api.auth import get_current_user
from secagents_api.schemas import TargetCreate, TargetResponse

router = APIRouter()


@router.post("", response_model=TargetResponse, status_code=201)
async def create_target(
    body: TargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target = Target(
        project_id=body.project_id,
        domain=body.domain,
        scope=body.scope or [body.domain],
        excluded=body.excluded,
        tags=body.tags,
        created_by=current_user.id
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("", response_model=List[TargetResponse])
async def list_targets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Target))
    return result.scalars().all()


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Target not found")
    return target
