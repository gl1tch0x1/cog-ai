.PHONY: all build test clean dev

all: build

# --- Build ---
build: build-rust build-go build-cpp build-python

build-cpp:
	cmake -B cpp-core/build -S cpp-core && cmake --build cpp-core/build

build-rust:
	cd rust-core && cargo build --release

build-go:
	cd go-services/recon && go build ./...
	cd go-services/scanners && go build ./...
	cd go-services/cli && go build -o bin/secagents-cli ./cmd

build-python:
	cd python-agents && pip install -e .

# --- Test ---
test: test-rust test-go test-cpp test-python

test-cpp:
	cd cpp-core/build && ctest --output-on-failure || true

test-rust:
	cd rust-core && cargo test

test-go:
	cd go-services/recon && go test ./...
	cd go-services/scanners && go test ./...

test-python:
	cd python-agents && pytest

# --- Docker ---
docker-up:
	docker compose up -d

docker-down:
	docker compose down

# --- Clean ---
clean:
	cd rust-core && cargo clean
	cd go-services/recon && go clean

