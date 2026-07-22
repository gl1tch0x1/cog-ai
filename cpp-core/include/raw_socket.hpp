#ifndef SECAGENT_RAW_SOCKET_HPP
#define SECAGENT_RAW_SOCKET_HPP

#include <string>

namespace SecAgentCore {

struct ProbeResult {
    bool open;
    int port;
    std::string banner;
    double latency_ms;
};

class RawSocketProber {
public:
    static ProbeResult probe_port(const std::string& host, int port, int timeout_ms = 1000);
};

} // namespace SecAgentCore

#endif // SECAGENT_RAW_SOCKET_HPP
