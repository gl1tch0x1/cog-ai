#ifndef SECAGENT_C_API_H
#define SECAGENT_C_API_H

#ifdef _WIN32
  #define SECAGENT_EXPORT __declspec(dllexport)
#else
  #define SECAGENT_EXPORT __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int open;
    int port;
    double latency_ms;
} SecAgentProbeResult;

SECAGENT_EXPORT int secagent_match_signature(const char* buffer, const char* pattern);
SECAGENT_EXPORT SecAgentProbeResult secagent_probe_port(const char* host, int port, int timeout_ms);

#ifdef __cplusplus
}
#endif

#endif // SECAGENT_C_API_H
