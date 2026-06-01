FROM golang:1.22-alpine AS builder
WORKDIR /app

# Copy workspace and module files to match go.work expectations
COPY go-services/go.work ./
COPY go-services/cli/go.mod ./cli/
COPY go-services/recon/go.mod ./recon/
COPY go-services/scanners/go.mod ./scanners/

# Copy locks if present
COPY go-services/cli/go.sum* ./cli/
COPY go-services/recon/go.sum* ./recon/
COPY go-services/scanners/go.sum* ./scanners/

RUN go mod download

# Copy the rest of the source
COPY go-services/cli ./cli
COPY go-services/recon ./recon
COPY go-services/scanners ./scanners

# Build the service
RUN CGO_ENABLED=0 go build -o /recon-service ./cli/cmd/main.go

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
COPY --from=builder /recon-service /usr/local/bin/recon-service
ENTRYPOINT ["recon-service"]
