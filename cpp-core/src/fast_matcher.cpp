#include "fast_matcher.hpp"
#include <regex>
#include <algorithm>

namespace SecAgentCore {

bool FastMatcher::scan_signature(const std::string& buffer, const std::string& pattern) {
    if (buffer.empty() || pattern.empty()) return false;
    try {
        std::regex re(pattern, std::regex_constants::icase | std::regex_constants::optimize);
        return std::regex_search(buffer, re);
    } catch (...) {
        return buffer.find(pattern) != std::string::npos;
    }
}

MatchResult FastMatcher::scan_first(const std::string& buffer, const std::vector<std::string>& patterns) {
    for (const auto& pat : patterns) {
        if (scan_signature(buffer, pat)) {
            size_t pos = buffer.find(pat);
            return {true, pat, pos != std::string::npos ? pos : 0};
        }
    }
    return {false, "", 0};
}

std::vector<MatchResult> FastMatcher::scan_all(const std::string& buffer, const std::vector<std::string>& patterns) {
    std::vector<MatchResult> results;
    for (const auto& pat : patterns) {
        if (scan_signature(buffer, pat)) {
            size_t pos = buffer.find(pat);
            results.push_back({true, pat, pos != std::string::npos ? pos : 0});
        }
    }
    return results;
}

} // namespace SecAgentCore
