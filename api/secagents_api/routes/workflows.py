"""Workflow management endpoints."""

import json
import os
import uuid
import datetime
import redis.asyncio as redis
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from secagents_api.database import get_db
from secagents_api.models import Workflow, User
from secagents_api.auth import get_current_user
from secagents_api.schemas import WorkflowStart, WorkflowResponse

router = APIRouter()
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url)


@router.post("/start", response_model=WorkflowResponse, status_code=201)
async def start_workflow(
    body: WorkflowStart,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workflow = Workflow(
        target_id=body.target_id,
        workflow_type=body.workflow_type,
        config=body.config,
        status="running",
        current_phase="recon",
        created_by=current_user.id
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    # Dispatch to Rust engine via Redis with strict schema and telemetry trace
    trace_id = str(uuid.uuid4())
    message = {
        "version": "1.0",
        "trace_id": trace_id,
        "workflow_id": str(workflow.id),
        "target_id": str(workflow.target_id),
        "type": workflow.workflow_type,
        "config": workflow.config or {},
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    try:
        await redis_client.publish("secagents_workflows", json.dumps(message))
        print(f"Dispatched workflow {workflow.id} with trace_id {trace_id}")
    except Exception as e:
        print(f"Failed to publish workflow to redis: {e}")
        
    return workflow


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Workflow))
    return result.scalars().all()


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workflow not found")
    return workflow
