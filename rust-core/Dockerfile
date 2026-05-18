FROM rust:1.78-slim AS builder
WORKDIR /app
COPY Cargo.toml ./
COPY rust-core/Cargo.toml ./rust-core/
# If there is a Cargo.lock at root, copy it. Use wildcard to ignore if missing.
COPY Cargo.lock* ./
COPY rust-core/src ./rust-core/src
RUN cargo build --release -p rust-core

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/secagents-core /usr/local/bin/secagents-core
ENTRYPOINT ["secagents-core"]
