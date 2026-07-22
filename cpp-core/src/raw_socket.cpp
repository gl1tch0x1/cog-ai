#include "raw_socket.hpp"
#include <chrono>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <fcntl.h>
#endif

namespace SecAgentCore {

ProbeResult RawSocketProber::probe_port(const std::string& host, int port, int timeout_ms) {
    auto start = std::chrono::high_resolution_clock::now();

#ifdef _WIN32
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);
#endif

    int sock = ::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock < 0) {
        return {false, port, "", 0.0};
    }

    struct sockaddr_in server;
    server.sin_family = AF_INET;
    server.sin_port = htons(port);
    inet_pton(AF_INET, host.c_str(), &server.sin_addr);

    // Set non-blocking socket
#ifdef _WIN32
    u_long mode = 1;
    ioctlsocket(sock, FIONBIO, &mode);
#else
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);
#endif

    int res = ::connect(sock, (struct sockaddr*)&server, sizeof(server));
    bool open = false;

    if (res < 0) {
        fd_set fdset;
        FD_ZERO(&fdset);
        FD_SET(sock, &fdset);

        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;

        if (select(sock + 1, NULL, &fdset, NULL, &tv) > 0) {
            int so_error;
            socklen_t len = sizeof(so_error);
            getsockopt(sock, SOL_SOCKET, SO_ERROR, (char*)&so_error, &len);
            if (so_error == 0) {
                open = true;
            }
        }
    } else {
        open = true;
    }

#ifdef _WIN32
    closesocket(sock);
    WSACleanup();
#else
    close(sock);
#endif

    auto elapsed = std::chrono::high_resolution_clock::now() - start;
    double latency = std::chrono::duration<double, std::milli>(elapsed).count();

    return {open, port, open ? "open" : "", latency};
}

} // namespace SecAgentCore
