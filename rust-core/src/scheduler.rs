use std::collections::VecDeque;
use std::sync::Arc;
use tokio::sync::{Mutex, Notify, Semaphore};
use uuid::Uuid;

use crate::engine::Task;

pub struct TaskScheduler {
    queue: Arc<Mutex<VecDeque<Task>>>,
    notify: Arc<Notify>,
    semaphore: Arc<Semaphore>,
    active: Arc<Mutex<usize>>,
}

impl TaskScheduler {
    pub fn new(max_concurrent: usize) -> Self {
        Self {
            queue: Arc::new(Mutex::new(VecDeque::new())),
            notify: Arc::new(Notify::new()),
            semaphore: Arc::new(Semaphore::new(max_concurrent)),
            active: Arc::new(Mutex::new(0)),
        }
    }

    pub async fn enqueue(&self, task: Task) {
        self.queue.lock().await.push_back(task);
        self.notify.notify_one();
    }

    pub async fn enqueue_batch(&self, tasks: Vec<Task>) {
        let mut q = self.queue.lock().await;
        for t in tasks {
            q.push_back(t);
        }
        self.notify.notify_waiters();
    }

    /// Dequeues a task, waiting for an available concurrency slot.
    pub async fn dequeue_blocking(&self) -> Option<Task> {
        // Wait for a slot first
        let _permit = match self.semaphore.acquire().await {
            Ok(p) => p,
            Err(_) => return None, // Semaphore closed
        };
        // Forget the permit because we manage the active count manually for now
        // or we could store the permit in a wrapper. 
        // To keep it simple and match the current API:
        _permit.forget(); 
        
        loop {
            let mut q = self.queue.lock().await;
            if let Some(t) = q.pop_front() {
                *self.active.lock().await += 1;
                return Some(t);
            }
            drop(q);
            // Wait for a task if queue was empty
            self.notify.notified().await;
        }
    }

    pub async fn dequeue(&self) -> Option<Task> {
        let _permit = self.semaphore.try_acquire().ok()?;
        let mut q = self.queue.lock().await;
        if let Some(t) = q.pop_front() {
            _permit.forget();
            *self.active.lock().await += 1;
            return Some(t);
        }
        None
    }

    pub async fn complete(&self, _task_id: Uuid) {
        let mut active = self.active.lock().await;
        *active = active.saturating_sub(1);
        self.semaphore.add_permits(1);
        self.notify.notify_one();
    }

    pub async fn pending_count(&self) -> usize {
        self.queue.lock().await.len()
    }

    pub async fn active_count(&self) -> usize {
        *self.active.lock().await
    }

    pub async fn wait_for_task(&self) {
        self.notify.notified().await;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::TaskState;

    fn make_task(name: &str) -> Task {
        Task {
            id: Uuid::new_v4(),
            name: name.into(),
            agent: "test".into(),
            state: TaskState::Queued,
            input: serde_json::json!({}),
            output: None,
            depends_on: vec![],
        }
    }

    #[tokio::test]
    async fn scheduler_respects_concurrency() {
        let sched = TaskScheduler::new(2);
        sched.enqueue(make_task("a")).await;
        sched.enqueue(make_task("b")).await;
        sched.enqueue(make_task("c")).await;

        let t1 = sched.dequeue().await.unwrap();
        let _t2 = sched.dequeue().await.unwrap();
        assert!(sched.dequeue().await.is_none()); // at max

        sched.complete(t1.id).await;
        assert!(sched.dequeue().await.is_some());
    }
}
