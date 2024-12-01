//�����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����`HttpParams`��`AuthScheme`��`AuthState`��`AuthPolicy`��`Log`��`LogFactory`����ͽӿ��Ѿ���C++��ʵ�֡�


#include <map>
#include <string>
#include <vector>
#include <stdexcept>
#include <algorithm>
#include <iterator>
#include <iostream>
#include <memory>

// ������Щ��ͽӿ��Ѿ���C++��ʵ��
class HttpParams;
class AuthScheme;
class AuthState;
class AuthPolicy;
class Log;
class LogFactory;

class AuthChallengeProcessor {
public:
    AuthChallengeProcessor(const std::shared_ptr<HttpParams>& params) {
        if (!params) {
            throw std::invalid_argument("Parameter collection may not be null");
        }
        this->params = params;
    }

    std::shared_ptr<AuthScheme> selectAuthScheme(const std::map<std::string, std::string>& challenges) {
        if (challenges.empty()) {
            throw std::invalid_argument("Challenge map may not be null");
        }

        auto authPrefs = params->getParameter(AuthPolicy::AUTH_SCHEME_PRIORITY);
        if (!authPrefs || authPrefs->empty()) {
            authPrefs = AuthPolicy::getDefaultAuthPrefs();
        }

        if (LOG->isDebugEnabled()) {
            std::string authPrefsStr;
            for (const auto& pref : *authPrefs) {
                authPrefsStr += pref + " ";
            }
            LOG->debug("Supported authentication schemes in the order of preference: " + authPrefsStr);
        }

        std::shared_ptr<AuthScheme> authscheme = nullptr;
        std::string challenge;

        for (const auto& id : *authPrefs) {
            auto it = challenges.find(toLower(id));
            if (it != challenges.end()) {
                challenge = it->second;
                if (LOG->isInfoEnabled()) {
                    LOG->info(id + " authentication scheme selected");
                }
                try {
                    authscheme = AuthPolicy::getAuthScheme(id);
                } catch (const std::exception& e) {
                    throw std::runtime_error(e.what());
                }
                break;
            } else {
                if (LOG->isDebugEnabled()) {
                    LOG->debug("Challenge for " + id + " authentication scheme not available");
                }
            }
        }

        if (!authscheme) {
            throw std::runtime_error("Unable to respond to any of these challenges: " + challengesToString(challenges));
        }

        return authscheme;
    }

    std::shared_ptr<AuthScheme> processChallenge(const std::shared_ptr<AuthState>& state, const std::map<std::string, std::string>& challenges) {
        if (!state) {
            throw std::invalid_argument("Authentication state may not be null");
        }
        if (challenges.empty()) {
            throw std::invalid_argument("Challenge map may not be null");
        }

        if (state->isPreemptive() || !state->getAuthScheme()) {
            state->setAuthScheme(selectAuthScheme(challenges));
        }

        auto authscheme = state->getAuthScheme();
        std::string id = authscheme->getSchemeName();

        if (LOG->isDebugEnabled()) {
            LOG->debug("Using authentication scheme: " + id);
        }

        auto it = challenges.find(toLower(id));
        if (it == challenges.end()) {
            throw std::runtime_error(id + " authorization challenge expected, but not found");
        }

        authscheme->processChallenge(it->second);
        LOG->debug("Authorization challenge processed");

        return authscheme;
    }

private:
    std::shared_ptr<HttpParams> params;
    static std::shared_ptr<Log> LOG;

    static std::string toLower(const std::string& str) {
        std::string lowerStr = str;
        std::transform(lowerStr.begin(), lowerStr.end(), lowerStr.begin(), ::tolower);
        return lowerStr;
    }

    static std::string challengesToString(const std::map<std::string, std::string>& challenges) {
        std::string result;
        for (const auto& pair : challenges) {
            result += pair.first + ": " + pair.second + ", ";
        }
        if (!result.empty()) {
            result.pop_back(); // Remove last comma
            result.pop_back();
        }
        return result;
    }
};

std::shared_ptr<Log> AuthChallengeProcessor::LOG = LogFactory::getLog("AuthChallengeProcessor");


// ### ˵����
// 1. **������**������`HttpParams`��`AuthScheme`��`AuthState`��`AuthPolicy`��`Log`��`LogFactory`����ͽӿ��Ѿ���C++��ʵ�֡�
// 2. **����ָ��**��ʹ��`std::shared_ptr`������������������ڣ������ڴ�й©��
// 3. **�쳣����**��ʹ��`std::invalid_argument`��`std::runtime_error`�������쳣�����
// 4. **��־��¼**������`Log`����`debug`��`info`��`isInfoEnabled`��`isDebugEnabled`�ȷ�����
// 5. **�ַ�������**��ʹ��`std::transform`�����ַ���ת��ΪСд��

// ���C++�����Ƕ�ӦJava�����ֱ�ӷ��룬��������������Ѿ���ȷʵ�֡�