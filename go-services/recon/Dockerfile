FROM golang:1.22-alpine AS builder
WORKDIR /app
# Copy workspace and module files
COPY go-services/go.work ./
COPY go-services/cli/go.mod ./go-services/cli/
COPY go-services/recon/go.mod ./go-services/recon/
COPY go-services/scanners/go.mod ./go-services/scanners/
# Copy locks if present
COPY go-services/cli/go.sum* ./go-services/cli/
COPY go-services/recon/go.sum* ./go-services/recon/
COPY go-services/scanners/go.sum* ./go-services/scanners/

RUN go mod download
COPY go-services ./go-services
RUN CGO_ENABLED=0 go build -o /recon-service ./go-services/cli/cmd/main.go

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
COPY --from=builder /recon-service /usr/local/bin/recon-service
ENTRYPOINT ["recon-service"]
