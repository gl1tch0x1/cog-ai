#include <iostream>
#include <string>
#include "fast_matcher.hpp"
#include "raw_socket.hpp"

int main(int argc, char* argv[]) {
    std::cout << "SecAgent C++ Foundational Core v0.3.0" << std::endl;

    if (argc >= 4 && std::string(argv[1]) == "--probe") {
        std::string host = argv[2];
        int port = std::stoi(argv[3]);
        auto res = SecAgentCore::RawSocketProber::probe_port(host, port);
        std::cout << "Probe Target: " << host << ":" << port 
                  << " | Open: " << (res.open ? "YES" : "NO") 
                  << " | Latency: " << res.latency_ms << "ms" << std::endl;
        return 0;
    }

    if (argc >= 4 && std::string(argv[1]) == "--match") {
        std::string buffer = argv[2];
        std::string pattern = argv[3];
        bool matched = SecAgentCore::FastMatcher::scan_signature(buffer, pattern);
        std::cout << "Buffer Match: " << (matched ? "MATCH FOUND" : "NO MATCH") << std::endl;
        return 0;
    }

    std::cout << "Usage:" << std::endl;
    std::cout << "  secagent_core_bin --probe <host> <port>" << std::endl;
    std::cout << "  secagent_core_bin --match <buffer> <pattern>" << std::endl;
    return 0;
}
