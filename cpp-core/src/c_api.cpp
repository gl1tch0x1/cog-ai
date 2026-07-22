#include "c_api.h"
#include "fast_matcher.hpp"
#include "raw_socket.hpp"

extern "C" {

SECAGENT_EXPORT int secagent_match_signature(const char* buffer, const char* pattern) {
    if (!buffer || !pattern) return 0;
    return SecAgentCore::FastMatcher::scan_signature(buffer, pattern) ? 1 : 0;
}

SECAGENT_EXPORT SecAgentProbeResult secagent_probe_port(const char* host, int port, int timeout_ms) {
    if (!host) return {0, port, 0.0};
    auto res = SecAgentCore::RawSocketProber::probe_port(host, port, timeout_ms);
    return {res.open ? 1 : 0, res.port, res.latency_ms};
}

}
