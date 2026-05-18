"""Integration tests for the FastAPI backend."""

import pytest
import uuid
import datetime
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from secagents_api.main import app
from secagents_api.auth import get_current_user
from secagents_api.database import get_db
from secagents_api.models import User, Target

# Mock authentication
dummy_user = User(id=uuid.uuid4(), email="test@example.com", role="analyst", is_active=True)
app.dependency_overrides[get_current_user] = lambda: dummy_user

# Mock database
async def override_get_db():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    
    async def fake_refresh(obj):
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime.datetime.now()
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()
            
    mock_session.refresh.side_effect = fake_refresh
    
    async def fake_execute(*args, **kwargs):
        query_str = str(args[0]).lower()
        res = MagicMock()
        if "from targets" in query_str:
            mock_target = Target(
                id=uuid.uuid4(),
                project_id=uuid.uuid4(),
                domain="example.com",
                scope=["*.example.com"],
                excluded=[],
                tags=[],
                created_at=datetime.datetime.now()
            )
            res.scalars.return_value.all.return_value = [mock_target]
        elif "from findings" in query_str:
            res.scalars.return_value.all.return_value = []
        elif "from reports" in query_str:
            res.scalar_one_or_none.return_value = None
        else:
            res.scalars.return_value.all.return_value = []
            res.scalar_one_or_none.return_value = None
        return res

    mock_session.execute.side_effect = fake_execute
    
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_list_targets(client):
    project_id = str(uuid.uuid4())
    resp = await client.post("/targets", json={"project_id": project_id, "domain": "example.com", "scope": ["*.example.com"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["domain"] == "example.com"

    resp = await client.get("/targets")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_start_workflow(client):
    # Create target first
    project_id = str(uuid.uuid4())
    target = await client.post("/targets", json={"project_id": project_id, "domain": "test.com"})
    target_id = target.json()["id"]

    resp = await client.post("/workflows/start", json={
        "target_id": target_id,
        "workflow_type": "bug_bounty",
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "running"


@pytest.mark.asyncio
async def test_findings_empty(client):
    resp = await client.get("/findings")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_report_not_found(client):
    resp = await client.get("/reports/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
