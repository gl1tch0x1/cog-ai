package recon

import (
	"context"
	"fmt"
	"net"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// Result holds a discovered subdomain with metadata.
type Result struct {
	Domain    string   `json:"domain"`
	IPs       []string `json:"ips,omitempty"`
	Source    string   `json:"source"`
	Timestamp int64    `json:"timestamp"`
}

// SubdomainEnumerator discovers subdomains using multiple techniques.
type SubdomainEnumerator struct {
	Resolvers   []string
	Timeout     time.Duration
	Concurrency int
	resolverIdx uint32
	pool        []*net.Resolver
}

func NewSubdomainEnumerator() *SubdomainEnumerator {
	resolvers := []string{"8.8.8.8:53", "1.1.1.1:53", "9.9.9.9:53", "64.6.64.6:53"}
	s := &SubdomainEnumerator{
		Resolvers:   resolvers,
		Timeout:     5 * time.Second,
		Concurrency: 50,
	}
	
	// Pre-create resolver pool
	for _, addr := range resolvers {
		addr := addr // capture
		s.pool = append(s.pool, &net.Resolver{
			PreferGo: true,
			Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
				d := net.Dialer{Timeout: s.Timeout}
				return d.DialContext(ctx, "udp", addr)
			},
		})
	}
	return s
}

func (s *SubdomainEnumerator) getNextResolver() *net.Resolver {
	idx := atomic.AddUint32(&s.resolverIdx, 1)
	return s.pool[idx%uint32(len(s.pool))]
}

// BruteForce performs DNS brute-force against a wordlist.
func (s *SubdomainEnumerator) BruteForce(ctx context.Context, domain string, wordlist []string) <-chan Result {
	results := make(chan Result, s.Concurrency*2)
	sem := make(chan struct{}, s.Concurrency)
	var wg sync.WaitGroup

	go func() {
		defer close(results)
		for _, word := range wordlist {
			select {
			case <-ctx.Done():
				return
			case sem <- struct{}{}:
			}
			wg.Add(1)
			go func(sub string) {
				defer wg.Done()
				defer func() { <-sem }()

				fqdn := fmt.Sprintf("%s.%s", sub, domain)
				ips, err := s.resolve(ctx, fqdn)
				if err == nil && len(ips) > 0 {
					select {
					case results <- Result{
						Domain:    fqdn,
						IPs:       ips,
						Source:    "bruteforce",
						Timestamp: time.Now().Unix(),
					}:
					case <-ctx.Done():
						return
					}
				}
			}(word)
		}
		wg.Wait()
	}()

	return results
}

func (s *SubdomainEnumerator) resolve(ctx context.Context, domain string) ([]string, error) {
	// Try up to 2 different resolvers on failure
	var lastErr error
	for i := 0; i < 2; i++ {
		resolver := s.getNextResolver()
		addrs, err := resolver.LookupHost(ctx, domain)
		if err == nil {
			return addrs, nil
		}
		lastErr = err
		
		// If context cancelled, stop immediately
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}
	}
	return nil, lastErr
}

// ParseWordlist splits newline-separated words.
func ParseWordlist(data string) []string {
	var words []string
	for _, line := range strings.Split(data, "\n") {
		w := strings.TrimSpace(line)
		if w != "" && !strings.HasPrefix(w, "#") {
			words = append(words, w)
		}
	}
	return words
}
