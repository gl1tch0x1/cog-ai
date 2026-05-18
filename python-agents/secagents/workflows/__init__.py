"""Workflow definitions for SecAgents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class WorkflowType(str, Enum):
    BUG_BOUNTY = "bug_bounty"
    PENTEST = "pentest"
    API_SECURITY = "api_security"
    CONTINUOUS_MONITORING = "continuous_monitoring"


@dataclass
class WorkflowStep:
    agent: str
    action: str
    depends_on: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    name: str
    workflow_type: WorkflowType
    steps: list[WorkflowStep]


BUG_BOUNTY_WORKFLOW = WorkflowDefinition(
    name="Bug Bounty Workflow",
    workflow_type=WorkflowType.BUG_BOUNTY,
    steps=[
        WorkflowStep(agent="planner", action="plan"),
        WorkflowStep(agent="recon", action="subdomain_enum", depends_on=["plan"]),
        WorkflowStep(agent="recon", action="http_probe", depends_on=["subdomain_enum"]),
        WorkflowStep(agent="recon", action="crawl", depends_on=["http_probe"]),
        WorkflowStep(agent="recon", action="param_discovery", depends_on=["crawl"]),
        WorkflowStep(agent="web_security", action="scan", depends_on=["param_discovery"]),
        WorkflowStep(agent="validator", action="validate", depends_on=["scan"]),
        WorkflowStep(agent="report", action="generate", depends_on=["validate"]),
    ],
)

PENTEST_WORKFLOW = WorkflowDefinition(
    name="Pentest Workflow",
    workflow_type=WorkflowType.PENTEST,
    steps=[
        WorkflowStep(agent="planner", action="plan"),
        WorkflowStep(agent="recon", action="full_recon", depends_on=["plan"]),
        WorkflowStep(agent="web_security", action="scan", depends_on=["full_recon"]),
        WorkflowStep(agent="api_security", action="scan", depends_on=["full_recon"]),
        WorkflowStep(agent="validator", action="validate", depends_on=["scan"]),
        WorkflowStep(agent="report", action="generate", depends_on=["validate"]),
    ],
)
