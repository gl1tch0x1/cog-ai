package recon

import (
	"context"
	"testing"
	"time"
)

func TestParseWordlist(t *testing.T) {
	data := "www\napi\n# comment\nmail\n"
	words := ParseWordlist(data)
	if len(words) != 3 {
		t.Fatalf("expected 3 words, got %d", len(words))
	}
}

func TestExtractParams(t *testing.T) {
	urls := []string{
		"https://example.com/search?q=test&page=1",
		"https://example.com/search?q=other",
	}
	results := ExtractParams(urls)
	if len(results) != 2 { // q and page (deduplicated)
		t.Fatalf("expected 2 params, got %d", len(results))
	}
}

func TestCrawlerInit(t *testing.T) {
	c := NewCrawler(2)
	if c.MaxDepth != 2 {
		t.Fatal("unexpected max depth")
	}
}

func TestHTTPProberInit(t *testing.T) {
	p := NewHTTPProber()
	if len(p.Ports) != 4 {
		t.Fatal("expected 4 default ports")
	}
}

func TestSubdomainEnumeratorTimeout(t *testing.T) {
	e := NewSubdomainEnumerator()
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()

	ch := e.BruteForce(ctx, "nonexistent.invalid", []string{"www"})
	count := 0
	for range ch {
		count++
	}
	// Should complete without hanging
}
