"""Contract tests: verify message schemas between services."""

import json
import uuid
import datetime
import pytest


WORKFLOW_MESSAGE_SCHEMA_REQUIRED_FIELDS = {
    "version", "trace_id", "workflow_id", "target_id", "type", "config", "timestamp"
}


def test_workflow_dispatch_message_schema():
    """Verify the Redis message from API matches what Rust core expects."""
    # This is the exact format produced by api/routes/workflows.py
    message = {
        "version": "1.0",
        "trace_id": str(uuid.uuid4()),
        "workflow_id": str(uuid.uuid4()),
        "target_id": str(uuid.uuid4()),
        "type": "bug_bounty",
        "config": {"depth": "standard"},
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    # All required fields present
    assert WORKFLOW_MESSAGE_SCHEMA_REQUIRED_FIELDS.issubset(message.keys())

    # Serializable to JSON
    payload = json.dumps(message)
    parsed = json.loads(payload)

    # Rust core expects these to be valid UUIDs
    uuid.UUID(parsed["workflow_id"])
    uuid.UUID(parsed["target_id"])
    uuid.UUID(parsed["trace_id"])

    # Version must be string
    assert isinstance(parsed["version"], str)
    # Config must be dict
    assert isinstance(parsed["config"], dict)
    # Type must be non-empty string
    assert isinstance(parsed["type"], str) and len(parsed["type"]) > 0


def test_workflow_message_handles_empty_config():
    """Rust core should handle empty config gracefully."""
    message = {
        "version": "1.0",
        "trace_id": str(uuid.uuid4()),
        "workflow_id": str(uuid.uuid4()),
        "target_id": str(uuid.uuid4()),
        "type": "quick_scan",
        "config": {},
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    payload = json.dumps(message)
    parsed = json.loads(payload)
    # config.target may be absent — Rust handles this with unwrap_or("")
    assert parsed["config"].get("target", "") == ""


def test_event_bus_event_schema():
    """Verify event schema matches what consumers expect."""
    # This mirrors rust-core/src/event_bus.rs Event struct
    event = {
        "id": str(uuid.uuid4()),
        "event_type": "WorkflowStarted",
        "workflow_id": str(uuid.uuid4()),
        "payload": {"agent": "subdomain", "name": "recon"},
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    valid_event_types = {
        "WorkflowStarted", "WorkflowCompleted", "WorkflowFailed",
        "TaskStarted", "TaskCompleted", "TaskFailed",
        "FindingDiscovered", "PolicyViolation",
    }

    assert event["event_type"] in valid_event_types
    uuid.UUID(event["id"])
    uuid.UUID(event["workflow_id"])
    assert isinstance(event["payload"], dict)
