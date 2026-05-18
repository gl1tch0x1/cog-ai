"""Supervisor agent for workflow coordination and approval."""

import logging
from enum import Enum
from typing import Optional

from secagents.agents.base import BaseAgent, AgentConfig, AgentOutput, AgentRole
from secagents.prompts import SUPERVISOR_PROMPT

logger = logging.getLogger(__name__)


class WorkflowPhase(str, Enum):
    """Workflow phases."""
    PLANNING = "planning"
    RECON = "recon"
    DISCOVERY = "discovery"
    TESTING = "testing"
    VALIDATION = "validation"
    REPORTING = "reporting"
    COMPLETE = "complete"


class SupervisorAgent(BaseAgent):
    """Coordinates all agents and approves phase transitions.
    
    Responsibilities:
    - Intent classification for incoming tasks
    - Task decomposition across multiple agents
    - Phase transition approval
    - Workflow state monitoring
    - Escalation and abort handling
    """

    def __init__(self):
        super().__init__(AgentConfig(
            role=AgentRole.SUPERVISOR,
            name="supervisor",
            tools=["approve_transition", "escalate", "abort", "classify_intent"],
            timeout_seconds=60.0,
        ))
        self.logger = logging.getLogger("secagents.supervisor")

    def system_prompt(self) -> str:
        """Return the supervisor's system prompt."""
        return SUPERVISOR_PROMPT

    async def execute(self, task: dict) -> AgentOutput:
        """Execute supervisor logic for workflow coordination."""
        action = task.get("action", "review")
        self.logger.info(f"Processing action: {action}")

        try:
            if action == "classify_intent":
                decision = self._classify_intent(task)
            elif action == "review":
                decision = self._review_phase(task.get("workflow_state", {}))
            elif action == "approve":
                decision = self._approve_transition(task)
            elif action == "abort":
                decision = self._abort_workflow(task)
            elif action == "escalate":
                decision = self._escalate_issue(task)
            else:
                decision = {"error": f"unknown action: {action}"}
                confidence = 0.0
        except Exception as e:
            self.logger.error(f"Error processing action {action}: {str(e)}", exc_info=True)
            decision = {"error": str(e)}
            confidence = 0.0
        else:
            confidence = self._calculate_confidence_for_decision(decision)

        return self._format_output(
            result=decision,
            confidence=confidence,
            reasoning=f"Supervisor processed action: {action}",
            metadata={"action": action},
        )

    def _classify_intent(self, task: dict) -> dict:
        """Classify incoming task intent.
        
        Args:
            task: Task containing user intent or objective
            
        Returns:
            Classification result with detected intent category
        """
        objective = task.get("objective", "").lower()
        scope = task.get("scope", {})
        
        # Intent classification logic
        if any(word in objective for word in ["recon", "enumerate", "discover"]):
            intent = "reconnaissance"
        elif any(word in objective for word in ["test", "scan", "vulnerability", "find"]):
            intent = "vulnerability_testing"
        elif any(word in objective for word in ["report", "generate", "document"]):
            intent = "reporting"
        elif any(word in objective for word in ["validate", "confirm", "verify"]):
            intent = "validation"
        else:
            intent = "general_testing"

        self.logger.info(f"Classified intent as: {intent}")
        
        return {
            "classified_intent": intent,
            "scope_valid": self._validate_scope(scope),
            "recommended_phases": self._recommend_phases(intent),
        }

    def _review_phase(self, state: dict) -> dict:
        """Review current phase and decide whether to proceed.
        
        Args:
            state: Current workflow state
            
        Returns:
            Decision on whether to advance or wait
        """
        current_phase = state.get("current_phase", "")
        completed_tasks = state.get("completed_tasks", 0)
        total_tasks = state.get("total_tasks", 1)
        failed_tasks = state.get("failed_tasks", 0)

        progress_ratio = completed_tasks / total_tasks if total_tasks > 0 else 0

        # Check for failure threshold
        if failed_tasks > 0:
            failure_ratio = failed_tasks / total_tasks
            if failure_ratio > 0.3:  # More than 30% failure rate
                self.logger.warning(f"High failure rate detected: {failure_ratio:.1%}")
                return {
                    "approved": False,
                    "action": "escalate",
                    "reason": f"High failure rate: {failure_ratio:.1%}",
                    "progress": f"{completed_tasks}/{total_tasks}",
                }

        # Check if phase complete
        if progress_ratio >= 1.0:
            self.logger.info(f"Phase '{current_phase}' complete, approving advancement")
            return {
                "approved": True,
                "action": "advance",
                "current_phase": current_phase,
                "next_phase": self._get_next_phase(current_phase),
            }

        return {
            "approved": False,
            "action": "wait",
            "current_phase": current_phase,
            "progress": f"{completed_tasks}/{total_tasks}",
            "completion_ratio": round(progress_ratio, 2),
        }

    def _approve_transition(self, task: dict) -> dict:
        """Approve phase transition with validation.
        
        Args:
            task: Transition request
            
        Returns:
            Approval decision with validation results
        """
        current_phase = task.get("from_phase", "")
        next_phase = task.get("to_phase", "")
        requirements = task.get("requirements", [])

        # Validate requirements
        valid = True
        unmet = []
        for req in requirements:
            if not task.get(f"completed_{req}", False):
                valid = False
                unmet.append(req)

        decision = {
            "approved": valid,
            "from_phase": current_phase,
            "to_phase": next_phase,
            "validation_passed": valid,
        }

        if not valid:
            decision["unmet_requirements"] = unmet
            self.logger.warning(f"Transition blocked: {unmet}")
        else:
            self.logger.info(f"Approving transition from {current_phase} to {next_phase}")

        return decision

    def _abort_workflow(self, task: dict) -> dict:
        """Abort workflow with reason.
        
        Args:
            task: Abort request
            
        Returns:
            Abort confirmation
        """
        reason = task.get("reason", "manual abort")
        workflow_id = task.get("workflow_id", "unknown")

        self.logger.warning(f"Aborting workflow {workflow_id}: {reason}")

        return {
            "approved": False,
            "action": "abort",
            "reason": reason,
            "workflow_id": workflow_id,
            "status": "aborted",
        }

    def _escalate_issue(self, task: dict) -> dict:
        """Escalate issue for manual review.
        
        Args:
            task: Escalation request
            
        Returns:
            Escalation confirmation
        """
        issue_type = task.get("issue_type", "unknown")
        details = task.get("details", "")
        severity = task.get("severity", "medium")

        self.logger.error(f"Escalating {issue_type} (severity: {severity}): {details}")

        return {
            "action": "escalate",
            "issue_type": issue_type,
            "severity": severity,
            "details": details,
            "requires_review": True,
        }

    def _validate_scope(self, scope: dict) -> bool:
        """Validate scope boundaries.
        
        Args:
            scope: Scope configuration
            
        Returns:
            True if scope is valid
        """
        required = ["target"]
        return all(scope.get(key) for key in required)

    def _recommend_phases(self, intent: str) -> list[str]:
        """Recommend workflow phases based on intent.
        
        Args:
            intent: Classified intent
            
        Returns:
            List of recommended phases
        """
        phase_mapping = {
            "reconnaissance": [
                WorkflowPhase.PLANNING.value,
                WorkflowPhase.RECON.value,
                WorkflowPhase.DISCOVERY.value,
            ],
            "vulnerability_testing": [
                WorkflowPhase.PLANNING.value,
                WorkflowPhase.RECON.value,
                WorkflowPhase.TESTING.value,
                WorkflowPhase.VALIDATION.value,
            ],
            "reporting": [
                WorkflowPhase.REPORTING.value,
            ],
            "validation": [
                WorkflowPhase.VALIDATION.value,
                WorkflowPhase.REPORTING.value,
            ],
            "general_testing": [
                WorkflowPhase.PLANNING.value,
                WorkflowPhase.RECON.value,
                WorkflowPhase.TESTING.value,
                WorkflowPhase.VALIDATION.value,
                WorkflowPhase.REPORTING.value,
            ],
        }
        return phase_mapping.get(intent, phase_mapping["general_testing"])

    def _get_next_phase(self, current_phase: str) -> Optional[str]:
        """Get next phase in workflow.
        
        Args:
            current_phase: Current phase name
            
        Returns:
            Next phase or None if at end
        """
        phases = [p.value for p in WorkflowPhase]
        try:
            idx = phases.index(current_phase)
            return phases[idx + 1] if idx + 1 < len(phases) else None
        except ValueError:
            return None

    def _calculate_confidence_for_decision(self, decision: dict) -> float:
        """Calculate confidence for supervisor decision.
        
        Args:
            decision: Decision result
            
        Returns:
            Confidence score 0.0-1.0
        """
        if "error" in decision:
            return 0.0
        if "approved" in decision:
            return 0.95 if decision["approved"] else 0.85
        if "action" in decision:
            return 0.9 if decision["action"] != "escalate" else 0.75
        return 0.8
