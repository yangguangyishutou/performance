//以下是将给定的Java代码翻译成C++的版本。假设相关的依赖项已经实现，例如`ParameterParser`、`NameValuePair`、`Header`等类已经在C++中实现。


#include <string>
#include <map>
#include <vector>
#include <stdexcept>
#include <algorithm>

// 假设这些类已经在C++中实现
class ParameterParser;
class NameValuePair;
class Header;

class MalformedChallengeException : public std::runtime_error {
public:
    MalformedChallengeException(const std::string& message) : std::runtime_error(message) {}
};

class AuthChallengeParser {
public:
    /**
     * Extracts authentication scheme from the given authentication challenge.
     *
     * @param challengeStr the authentication challenge string
     * @return authentication scheme
     * 
     * @throws MalformedChallengeException when the authentication challenge string
     *  is malformed
     */
    static std::string extractScheme(const std::string& challengeStr) {
        if (challengeStr.empty()) {
            throw std::invalid_argument("Challenge may not be null");
        }
        size_t idx = challengeStr.find(' ');
        std::string s;
        if (idx == std::string::npos) {
            s = challengeStr;
        } else {
            s = challengeStr.substr(0, idx);
        }
        if (s.empty()) {
            throw MalformedChallengeException("Invalid challenge: " + challengeStr);
        }
        std::transform(s.begin(), s.end(), s.begin(), ::tolower);
        return s;
    }

    /**
     * Extracts a map of challenge parameters from an authentication challenge.
     * Keys in the map are lower-cased
     *
     * @param challengeStr the authentication challenge string
     * @return a map of authentication challenge parameters
     * @throws MalformedChallengeException when the authentication challenge string
     *  is malformed
     */
    static std::map<std::string, std::string> extractParams(const std::string& challengeStr) {
        if (challengeStr.empty()) {
            throw std::invalid_argument("Challenge may not be null");
        }
        size_t idx = challengeStr.find(' ');
        if (idx == std::string::npos) {
            throw MalformedChallengeException("Invalid challenge: " + challengeStr);
        }
        std::map<std::string, std::string> map;
        ParameterParser parser;
        std::vector<NameValuePair> params = parser.parse(challengeStr.substr(idx + 1), ',');
        for (const auto& param : params) {
            std::string name = param.getName();
            std::transform(name.begin(), name.end(), name.begin(), ::tolower);
            map[name] = param.getValue();
        }
        return map;
    }

    /**
     * Extracts a map of challenges ordered by authentication scheme name
     *
     * @param headers the array of authorization challenges
     * @return a map of authorization challenges
     * 
     * @throws MalformedChallengeException if any of challenge strings
     *  is malformed
     */
    static std::map<std::string, std::string> parseChallenges(const std::vector<Header>& headers) {
        if (headers.empty()) {
            throw std::invalid_argument("Array of challenges may not be null");
        }
        std::map<std::string, std::string> challengemap;
        for (const auto& header : headers) {
            std::string challenge = header.getValue();
            std::string scheme = AuthChallengeParser::extractScheme(challenge);
            challengemap[scheme] = challenge;
        }
        return challengemap;
    }
};


// ### 说明：
// 1. **异常处理**：在C++中，异常处理使用`std::runtime_error`和`std::invalid_argument`来替代Java中的`MalformedChallengeException`和`IllegalArgumentException`。
// 2. **字符串处理**：C++中的字符串处理使用`std::string`，并且使用`std::transform`来实现字符串的小写转换。
// 3. **容器**：C++中的`std::map`和`std::vector`分别替代了Java中的`HashMap`和`List`。
// 4. **假设依赖项**：假设`ParameterParser`、`NameValuePair`和`Header`类已经在C++中实现，并且具有与Java版本相同的功能。

// 这个C++代码应该能够实现与原始Java代码相同的功能。