.PHONY: all build test clean dev

all: build

# --- Build ---
build: build-rust build-go build-python build-frontend

build-rust:
	cd rust-core && cargo build --release

build-go:
	cd go-services/recon && go build ./...
	cd go-services/scanners && go build ./...
	cd go-services/cli && go build -o bin/secagents-cli ./cmd

build-python:
	cd python-agents && pip install -e .
	cd api && pip install -e .

build-frontend:
	cd frontend/apex && npm ci && npm run build

# --- Test ---
test: test-rust test-go test-python

test-rust:
	cd rust-core && cargo test

test-go:
	cd go-services/recon && go test ./...
	cd go-services/scanners && go test ./...

test-python:
	cd python-agents && pytest
	cd api && pytest

# --- Dev ---
dev-api:
	cd api && uvicorn secagents_api.main:app --reload --port 8000

dev-frontend:
	cd frontend/apex && npm run dev

# --- Docker ---
docker-up:
	docker compose up -d

docker-down:
	docker compose down

# --- Clean ---
clean:
	cd rust-core && cargo clean
	cd go-services/recon && go clean
	rm -rf frontend/apex/.next
