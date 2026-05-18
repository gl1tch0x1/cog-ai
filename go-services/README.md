# Go Services

High-performance reconnaissance and scanning services.

## Modules

### recon/
- `subdomain.go` — DNS brute-force with concurrent resolution
- `httpprobe.go` — Multi-port HTTP/HTTPS probing
- `crawler.go` — Recursive link-following crawler with depth control
- `params.go` — Parameter discovery via brute-force and extraction

### scanners/
- `port_scanner.go` — TCP connect scanner with concurrency control

### cli/
- `cmd/main.go` — Unified CLI: `secagents-cli -cmd <subdomain|probe|crawl|portscan> -target <target>`

## Build & Test

```bash
cd recon && go test ./...
cd ../cli && go build -o bin/secagents-cli ./cmd
```
