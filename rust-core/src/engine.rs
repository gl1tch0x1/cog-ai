use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;

use crate::state::{TaskState, WorkflowContext, WorkflowState};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: Uuid,
    pub name: String,
    pub agent: String,
    pub state: TaskState,
    pub input: serde_json::Value,
    pub output: Option<serde_json::Value>,
    pub depends_on: Vec<Uuid>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowDef {
    pub id: Uuid,
    pub name: String,
    pub phases: Vec<Phase>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Phase {
    pub name: String,
    pub tasks: Vec<Task>,
}

#[async_trait]
pub trait TaskExecutor: Send + Sync {
    async fn execute(&self, task: &Task) -> Result<serde_json::Value, EngineError>;
}

#[derive(Debug, thiserror::Error)]
pub enum EngineError {
    #[error("invalid state transition: {0} -> {1}")]
    InvalidTransition(String, String),
    #[error("task failed: {0}")]
    TaskFailed(String),
    #[error("policy violation: {0}")]
    PolicyViolation(String),
    #[error("workflow {0} not found")]
    WorkflowNotFound(Uuid),
    #[error("task {0} not found in workflow {1}")]
    TaskNotFound(Uuid, Uuid),
}

pub struct WorkflowEngine {
    workflows: Arc<RwLock<HashMap<Uuid, WorkflowContext>>>,
}

impl WorkflowEngine {
    pub fn new() -> Self {
        Self {
            workflows: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn start_workflow(&self, def: &WorkflowDef) -> Result<Uuid, EngineError> {
        let ctx = WorkflowContext {
            workflow_id: def.id,
            state: WorkflowState::Running,
            current_phase: def.phases.first().map(|p| p.name.clone()).unwrap_or_default(),
            variables: serde_json::json!({}),
        };
        self.workflows.write().await.insert(def.id, ctx);
        Ok(def.id)
    }

    pub async fn transition(
        &self,
        workflow_id: Uuid,
        new_state: WorkflowState,
    ) -> Result<(), EngineError> {
        let mut workflows = self.workflows.write().await;
        let ctx = workflows.get_mut(&workflow_id).ok_or_else(|| {
            EngineError::WorkflowNotFound(workflow_id)
        })?;

        if !ctx.state.can_transition_to(&new_state) {
            return Err(EngineError::InvalidTransition(
                format!("{:?}", ctx.state),
                format!("{:?}", new_state),
            ));
        }
        ctx.state = new_state;
        Ok(())
    }

    pub async fn get_state(&self, workflow_id: Uuid) -> Option<WorkflowState> {
        self.workflows.read().await.get(&workflow_id).map(|c| c.state.clone())
    }

    pub async fn update_variables(&self, workflow_id: Uuid, vars: serde_json::Value) -> Result<(), EngineError> {
        let mut workflows = self.workflows.write().await;
        let ctx = workflows.get_mut(&workflow_id).ok_or_else(|| {
            EngineError::WorkflowNotFound(workflow_id)
        })?;
        
        if let Some(obj) = ctx.variables.as_object_mut() {
            if let Some(new_obj) = vars.as_object() {
                for (k, v) in new_obj {
                    obj.insert(k.clone(), v.clone());
                }
            }
        } else {
            ctx.variables = vars;
        }
        Ok(())
    }
}

impl Default for WorkflowEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn workflow_lifecycle() {
        let engine = WorkflowEngine::new();
        let def = WorkflowDef {
            id: Uuid::new_v4(),
            name: "test".into(),
            phases: vec![Phase { name: "recon".into(), tasks: vec![] }],
        };

        let id = engine.start_workflow(&def).await.unwrap();
        assert_eq!(engine.get_state(id).await, Some(WorkflowState::Running));

        engine.transition(id, WorkflowState::Completed).await.unwrap();
        assert_eq!(engine.get_state(id).await, Some(WorkflowState::Completed));
    }
}
