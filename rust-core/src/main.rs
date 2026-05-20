use rust_core::{
    engine::{Task, WorkflowDef, WorkflowEngine, Phase},
    event_bus::{Event, EventBus, EventType},
    policy::Policy,
    scheduler::TaskScheduler,
    state::TaskState,
};
use tracing_subscriber::EnvFilter;
use std::env;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Mutex;
use uuid::Uuid;
use futures_util::StreamExt;

const RECONNECT_DELAY_SECS: &[u64] = &[1, 2, 4, 8, 16, 30];

/// Simple token-bucket rate limiter
struct RateLimiter {
    tokens: f64,
    capacity: f64,
    refill_per_sec: f64,
    last_refill: Instant,
}

impl RateLimiter {
    fn new(max_per_sec: u32) -> Self {
        let cap = max_per_sec as f64;
        Self { tokens: cap, capacity: cap, refill_per_sec: cap, last_refill: Instant::now() }
    }

    async fn acquire(&mut self) {
        loop {
            let elapsed = self.last_refill.elapsed().as_secs_f64();
            self.tokens = (self.tokens + elapsed * self.refill_per_sec).min(self.capacity);
            self.last_refill = Instant::now();
            if self.tokens >= 1.0 {
                self.tokens -= 1.0;
                return;
            }
            let wait = (1.0 - self.tokens) / self.refill_per_sec;
            tokio::time::sleep(Duration::from_secs_f64(wait)).await;
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let filter = EnvFilter::from_default_env()
        .add_directive("rust_core=info".parse().unwrap_or_else(|_| "info".parse().unwrap()));
    tracing_subscriber::fmt().with_env_filter(filter).init();
    tracing::info!("SecAgents Rust Core starting");

    let engine = Arc::new(WorkflowEngine::new());
    let bus = Arc::new(EventBus::new(4096));
    let scheduler = Arc::new(TaskScheduler::new(16));
    let policy = load_policy();
    let rate_limiter = Arc::new(Mutex::new(RateLimiter::new(policy.max_requests_per_second)));

    // Worker loop
    let w_sched = Arc::clone(&scheduler);
    let w_bus = Arc::clone(&bus);
    let w_rl = Arc::clone(&rate_limiter);
    tokio::spawn(async move {
        loop {
            if let Some(task) = w_sched.dequeue_blocking().await {
                // Enforce rate limit before dispatching
                w_rl.lock().await.acquire().await;
                tracing::info!(task_id = %task.id, agent = %task.agent, "Dispatching task");
                w_bus.publish(Event::new(
                    EventType::TaskStarted, task.id,
                    serde_json::json!({"agent": task.agent, "name": task.name}),
                )).await;
                w_sched.complete(task.id).await;
                w_bus.publish(Event::new(
                    EventType::TaskCompleted, task.id, serde_json::json!({"agent": task.agent}),
                )).await;
            }
        }
    });

    let redis_url = env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379/1".to_string());

    // Reconnection loop
    let mut attempt = 0usize;
    loop {
        tracing::info!("Connecting to Redis (attempt {})", attempt + 1);
        match connect_and_listen(&redis_url, &engine, &scheduler, &bus, &policy).await {
            Ok(()) => break, // Graceful shutdown
            Err(e) => {
                let delay = RECONNECT_DELAY_SECS[attempt.min(RECONNECT_DELAY_SECS.len() - 1)];
                tracing::warn!("Redis connection lost: {}. Reconnecting in {}s", e, delay);
                tokio::time::sleep(Duration::from_secs(delay)).await;
                attempt += 1;
            }
        }
    }

    tracing::info!("SecAgents Rust Core stopped");
    Ok(())
}

async fn connect_and_listen(
    redis_url: &str,
    engine: &WorkflowEngine,
    scheduler: &TaskScheduler,
    bus: &EventBus,
    policy: &Policy,
) -> Result<(), Box<dyn std::error::Error>> {
    let client = redis::Client::open(redis_url)?;
    let con = client.get_async_connection().await?;
    let mut pubsub = con.into_pubsub();
    pubsub.subscribe("secagents_workflows").await?;
    tracing::info!("Subscribed to 'secagents_workflows'");

    let mut stream = pubsub.on_message();
    loop {
        tokio::select! {
            msg = stream.next() => {
                let Some(msg) = msg else { return Err("Stream ended".into()); };
                let payload: String = msg.get_payload()?;
                if let Err(e) = handle_message(&payload, engine, scheduler, bus, policy).await {
                    tracing::error!("Message handling failed: {}", e);
                }
            }
            _ = tokio::signal::ctrl_c() => {
                tracing::info!("Ctrl-C received");
                return Ok(());
            }
        }
    }
}

async fn handle_message(
    payload: &str,
    engine: &WorkflowEngine,
    scheduler: &TaskScheduler,
    bus: &EventBus,
    policy: &Policy,
) -> Result<(), Box<dyn std::error::Error>> {
    let json: serde_json::Value = serde_json::from_str(payload)?;
    let workflow_id = json["workflow_id"].as_str()
        .and_then(|s| s.parse::<Uuid>().ok())
        .unwrap_or_else(Uuid::new_v4);
    let target = json["config"]["target"].as_str().or(json["target_id"].as_str()).unwrap_or("");

    if !target.is_empty() {
        policy.check_domain(target)?;
    }

    let def = WorkflowDef {
        id: workflow_id,
        name: json["type"].as_str().unwrap_or("scan").to_string(),
        phases: vec![
            Phase { name: "recon".into(), tasks: vec![make_task("recon", "subdomain")] },
            Phase { name: "scan".into(), tasks: vec![make_task("scan", "security")] },
            Phase { name: "validate".into(), tasks: vec![make_task("validate", "validator")] },
            Phase { name: "report".into(), tasks: vec![make_task("report", "report")] },
        ],
    };

    engine.start_workflow(&def).await?;
    bus.publish(Event::new(EventType::WorkflowStarted, workflow_id, json.clone())).await;
    let tasks: Vec<Task> = def.phases.into_iter().flat_map(|p| p.tasks).collect();
    scheduler.enqueue_batch(tasks).await;
    tracing::info!(workflow_id = %workflow_id, "Workflow dispatched");
    Ok(())
}

fn make_task(name: &str, agent: &str) -> Task {
    Task {
        id: Uuid::new_v4(),
        name: name.into(),
        agent: agent.into(),
        state: TaskState::Queued,
        input: serde_json::json!({}),
        output: None,
        depends_on: vec![],
    }
}

fn load_policy() -> Policy {
    let allowed: Vec<String> = env::var("ALLOWED_DOMAINS")
        .unwrap_or_default()
        .split(',')
        .map(|s| s.trim().to_lowercase())
        .filter(|s| !s.is_empty())
        .collect();
    Policy {
        allowed_domains: allowed.into_iter().collect(),
        ..Policy::default()
    }
}
