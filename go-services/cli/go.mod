module github.com/secagents/go-services/cli

go 1.22

require (
	github.com/secagents/go-services/recon v0.0.0
	github.com/secagents/go-services/scanners v0.0.0
)

replace (
	github.com/secagents/go-services/recon => ../recon
	github.com/secagents/go-services/scanners => ../scanners
)
