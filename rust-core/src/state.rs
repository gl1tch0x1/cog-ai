use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum WorkflowState {
    Pending,
    Running,
    Paused,
    Completed,
    Failed,
    Cancelled,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum TaskState {
    Queued,
    Running,
    Success,
    Failed,
    Skipped,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowContext {
    pub workflow_id: Uuid,
    pub state: WorkflowState,
    pub current_phase: String,
    pub variables: serde_json::Value,
}

impl WorkflowState {
    pub fn can_transition_to(&self, next: &WorkflowState) -> bool {
        matches!(
            (self, next),
            (Self::Pending, Self::Running)
                | (Self::Running, Self::Paused)
                | (Self::Running, Self::Completed)
                | (Self::Running, Self::Failed)
                | (Self::Running, Self::Cancelled)
                | (Self::Paused, Self::Running)
                | (Self::Paused, Self::Cancelled)
        )
    }
}

impl TaskState {
    pub fn is_terminal(&self) -> bool {
        matches!(self, Self::Success | Self::Failed | Self::Skipped)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_transitions() {
        assert!(WorkflowState::Pending.can_transition_to(&WorkflowState::Running));
        assert!(WorkflowState::Running.can_transition_to(&WorkflowState::Completed));
        assert!(!WorkflowState::Completed.can_transition_to(&WorkflowState::Running));
    }

    #[test]
    fn terminal_states() {
        assert!(TaskState::Success.is_terminal());
        assert!(!TaskState::Running.is_terminal());
    }
}
