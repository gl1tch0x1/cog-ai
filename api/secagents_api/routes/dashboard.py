"""Dashboard stats with authorization filtering."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from secagents_api.database import get_db
from secagents_api.models import Finding, Workflow, Target, User
from secagents_api.auth import get_current_user

router = APIRouter()


class DashboardStats(BaseModel):
    active_workflows: int
    total_findings: int
    validated_findings: int
    total_targets: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = current_user.id
    user_targets = select(Target.id).where(Target.created_by == uid)

    active = await db.execute(
        select(func.count(Workflow.id)).where(
            Workflow.created_by == uid, Workflow.status == "running"
        )
    )
    total_f = await db.execute(
        select(func.count(Finding.id)).where(Finding.target_id.in_(user_targets))
    )
    valid_f = await db.execute(
        select(func.count(Finding.id)).where(
            Finding.target_id.in_(user_targets),
            Finding.validated == True,  # noqa: E712
        )
    )
    targets = await db.execute(
        select(func.count(Target.id)).where(Target.created_by == uid)
    )

    return DashboardStats(
        active_workflows=active.scalar() or 0,
        total_findings=total_f.scalar() or 0,
        validated_findings=valid_f.scalar() or 0,
        total_targets=targets.scalar() or 0,
    )
