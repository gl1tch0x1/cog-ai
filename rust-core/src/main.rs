use rust_core::{engine::WorkflowEngine, event_bus::EventBus, policy::Policy, scheduler::TaskScheduler};
use tracing_subscriber::EnvFilter;
use std::env;
use redis::AsyncCommands;
use futures_util::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("rust_core=info".parse().unwrap()))
        .init();

    tracing::info!("SecAgents Rust Core starting");

    let _engine = WorkflowEngine::new();
    let _bus = EventBus::new(4096);
    let _scheduler = TaskScheduler::new(16);
    let _policy = Policy::default();

    let redis_url = env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379/0".to_string());
    
    tracing::info!("Connecting to Redis at {}", redis_url);
    
    // Setup Redis connection and pubsub
    let client = redis::Client::open(redis_url)?;
    
    let mut con = match client.get_async_connection().await {
        Ok(c) => c,
        Err(e) => {
            tracing::error!("Failed to connect to Redis: {}", e);
            tracing::info!("Running in degraded mode without Redis connection");
            tokio::signal::ctrl_c().await.ok();
            tracing::info!("Shutting down");
            return Ok(());
        }
    };

    let mut pubsub = con.into_pubsub();
    if let Err(e) = pubsub.subscribe("secagents_workflows").await {
        tracing::error!("Failed to subscribe to channel: {}", e);
        return Err(e.into());
    }

    tracing::info!("All subsystems initialized, awaiting tasks via Redis channel 'secagents_workflows'");
    
    let mut message_stream = pubsub.on_message();

    loop {
        tokio::select! {
            msg = message_stream.next() => {
                if let Some(msg) = msg {
                    let payload: String = match msg.get_payload() {
                        Ok(p) => p,
                        Err(e) => {
                            tracing::error!("Failed to get message payload: {}", e);
                            continue;
                        }
                    };
                    
                    match serde_json::from_str::<serde_json::Value>(&payload) {
                        Ok(json) => {
                            let trace_id = json["trace_id"].as_str().unwrap_or("unknown");
                            let workflow_id = json["workflow_id"].as_str().unwrap_or("unknown");
                            tracing::info!(trace_id = %trace_id, workflow_id = %workflow_id, "Received valid workflow command");
                            // Pass trace_id and workflow_id into engine for correlated processing
                        },
                        Err(e) => {
                            tracing::error!("Invalid schema received: {}. Payload: {}", e, payload);
                        }
                    }
                } else {
                    tracing::warn!("Redis stream disconnected");
                    break;
                }
            }
            _ = tokio::signal::ctrl_c() => {
                tracing::info!("Received Ctrl-C, initiating graceful shutdown");
                break;
            }
        }
    }

    tracing::info!("Shutting down SecAgents Rust Core");
    Ok(())
}
