"""Workflow management endpoints with authorization filtering."""

import json
import os
import uuid
import datetime
import logging
from typing import List
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from secagents_api.database import get_db
from secagents_api.models import Workflow, User
from secagents_api.auth import get_current_user
from secagents_api.schemas import WorkflowStart, WorkflowResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_redis_pool: aioredis.Redis | None = None


def _get_redis_pool() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(_redis_url, decode_responses=True)
    return _redis_pool


@router.post("/start", response_model=WorkflowResponse, status_code=201)
async def start_workflow(
    body: WorkflowStart,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow = Workflow(
        target_id=body.target_id,
        workflow_type=body.workflow_type,
        config=body.config,
        status="pending",
        current_phase="queued",
        created_by=current_user.id,
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    trace_id = str(uuid.uuid4())
    message = {
        "version": "1.0",
        "trace_id": trace_id,
        "workflow_id": str(workflow.id),
        "target_id": str(workflow.target_id),
        "type": workflow.workflow_type,
        "config": workflow.config or {},
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    try:
        pool = _get_redis_pool()
        await pool.publish("secagents_workflows", json.dumps(message))
        workflow.status = "running"
        workflow.current_phase = "recon"
        await db.commit()
        await db.refresh(workflow)
        logger.info("Dispatched workflow %s trace=%s", workflow.id, trace_id)
    except Exception as e:
        logger.warning("Redis publish failed: %s — workflow remains pending", e)
        # Workflow stays in "pending" status — can be retried

    return workflow


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(Workflow.created_by == current_user.id)
    )
    return result.scalars().all()


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id, Workflow.created_by == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workflow not found")
    return workflow
