use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::sync::Arc;
use tokio::sync::broadcast;
use tokio::sync::RwLock;
use uuid::Uuid;

const DEFAULT_MAX_HISTORY: usize = 10_000;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub id: Uuid,
    pub event_type: EventType,
    pub workflow_id: Uuid,
    pub payload: serde_json::Value,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum EventType {
    WorkflowStarted,
    WorkflowCompleted,
    WorkflowFailed,
    TaskStarted,
    TaskCompleted,
    TaskFailed,
    FindingDiscovered,
    PolicyViolation,
}

pub struct EventBus {
    sender: broadcast::Sender<Event>,
    history: Arc<RwLock<VecDeque<Event>>>,
    max_history: usize,
}

impl EventBus {
    pub fn new(capacity: usize) -> Self {
        let (sender, _) = broadcast::channel(capacity);
        Self {
            sender,
            history: Arc::new(RwLock::new(VecDeque::with_capacity(DEFAULT_MAX_HISTORY))),
            max_history: DEFAULT_MAX_HISTORY,
        }
    }

    pub async fn publish(&self, event: Event) {
        let mut history = self.history.write().await;
        if history.len() >= self.max_history {
            history.pop_front();
        }
        history.push_back(event.clone());
        drop(history);
        let _ = self.sender.send(event);
    }

    pub fn subscribe(&self) -> broadcast::Receiver<Event> {
        self.sender.subscribe()
    }

    pub async fn history(&self) -> Vec<Event> {
        self.history.read().await.iter().cloned().collect()
    }

    pub async fn history_for_workflow(&self, workflow_id: Uuid) -> Vec<Event> {
        self.history
            .read()
            .await
            .iter()
            .filter(|e| e.workflow_id == workflow_id)
            .cloned()
            .collect()
    }

    pub async fn len(&self) -> usize {
        self.history.read().await.len()
    }
}

impl Event {
    pub fn new(event_type: EventType, workflow_id: Uuid, payload: serde_json::Value) -> Self {
        Self {
            id: Uuid::new_v4(),
            event_type,
            workflow_id,
            payload,
            timestamp: chrono::Utc::now(),
        }
    }
}

impl Default for EventBus {
    fn default() -> Self {
        Self::new(1024)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn pub_sub() {
        let bus = EventBus::new(16);
        let mut rx = bus.subscribe();

        let wf_id = Uuid::new_v4();
        let event = Event::new(EventType::WorkflowStarted, wf_id, serde_json::json!({}));
        bus.publish(event.clone()).await;

        let received = rx.recv().await.unwrap();
        assert_eq!(received.event_type, EventType::WorkflowStarted);
        assert_eq!(bus.history().await.len(), 1);
    }

    #[tokio::test]
    async fn ring_buffer_trims() {
        let mut bus = EventBus::new(16);
        bus.max_history = 3;

        let wf_id = Uuid::new_v4();
        for _ in 0..5 {
            bus.publish(Event::new(EventType::TaskStarted, wf_id, serde_json::json!({}))).await;
        }

        assert_eq!(bus.len().await, 3);
    }
}
