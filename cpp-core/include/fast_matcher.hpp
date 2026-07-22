#ifndef SECAGENT_FAST_MATCHER_HPP
#define SECAGENT_FAST_MATCHER_HPP

#include <string>
#include <vector>

namespace SecAgentCore {

struct MatchResult {
    bool matched;
    std::string pattern;
    size_t position;
};

class FastMatcher {
public:
    static bool scan_signature(const std::string& buffer, const std::string& pattern);
    static MatchResult scan_first(const std::string& buffer, const std::vector<std::string>& patterns);
    static std::vector<MatchResult> scan_all(const std::string& buffer, const std::vector<std::string>& patterns);
};

} // namespace SecAgentCore

#endif // SECAGENT_FAST_MATCHER_HPP
