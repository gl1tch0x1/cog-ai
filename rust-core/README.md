# Rust Core

Workflow orchestration engine for SecAgents.

## Components

- **engine.rs** — Workflow lifecycle management (start, transition, query)
- **state.rs** — State machine with validated transitions (Pending → Running → Completed/Failed)
- **event_bus.rs** — Pub/sub event system with history
- **scheduler.rs** — Concurrent task queue with configurable parallelism
- **policy.rs** — Domain/port enforcement, scope validation

## Build & Test

```bash
cargo build --release
cargo test
```

## State Machine

```
Pending → Running → Completed
                  → Failed
                  → Cancelled
         Running ↔ Paused
```
