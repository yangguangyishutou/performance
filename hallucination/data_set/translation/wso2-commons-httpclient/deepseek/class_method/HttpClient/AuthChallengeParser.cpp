

#include <string>
#include <map>
#include <vector>
#include <stdexcept>
#include <algorithm>

// ������Щ���Ѿ���C++��ʵ��
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


// ### ˵����
// 1. **�쳣����**����C++�У��쳣����ʹ��`std::runtime_error`��`std::invalid_argument`�����Java�е�`MalformedChallengeException`��`IllegalArgumentException`��
// 2. **�ַ�������**��C++�е��ַ�������ʹ��`std::string`������ʹ��`std::transform`��ʵ���ַ�����Сдת����
// 3. **����**��C++�е�`std::map`��`std::vector`�ֱ������Java�е�`HashMap`��`List`��
// 4. **����������**������`ParameterParser`��`NameValuePair`��`Header`���Ѿ���C++��ʵ�֣����Ҿ�����Java�汾��ͬ�Ĺ��ܡ�

// ���C++����Ӧ���ܹ�ʵ����ԭʼJava������ͬ�Ĺ��ܡ�