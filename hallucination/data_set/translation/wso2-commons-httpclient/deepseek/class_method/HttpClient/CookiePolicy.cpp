//�����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����C++���Ѿ�ʵ��������Java��`Map`��`Log`��`LogFactory`����ͽӿڡ�


#include <map>
#include <string>
#include <stdexcept>
#include <memory>
#include <vector>
#include <algorithm>
#include <mutex>
#include <iostream>

// �����Ѿ�ʵ��������Java��Log��LogFactory
class Log {
public:
    void error(const std::string& message, const std::exception& e) {
        std::cerr << "ERROR: " << message << " - " << e.what() << std::endl;
    }

    void warn(const std::string& message) {
        std::cerr << "WARN: " << message << std::endl;
    }
};

class LogFactory {
public:
    static Log* getLog(const std::string& className) {
        // ����LogFactory�᷵��һ��Logʵ��
        static Log log;
        return &log;
    }
};

// �����Ѿ�ʵ��������Java��CookieSpec�ӿ�
class CookieSpec {
public:
    virtual ~CookieSpec() = default;
    // ��������...
};

// �����Ѿ�ʵ��������Java�ľ���CookieSpec��
class RFC2109Spec : public CookieSpec {
    // ʵ��ϸ��...
};

class RFC2965Spec : public CookieSpec {
    // ʵ��ϸ��...
};

class CookieSpecBase : public CookieSpec {
    // ʵ��ϸ��...
};

class NetscapeDraftSpec : public CookieSpec {
    // ʵ��ϸ��...
};

class IgnoreCookiesSpec : public CookieSpec {
    // ʵ��ϸ��...
};

class CookiePolicy {
private:
    static std::map<std::string, std::shared_ptr<CookieSpec>> SPECS;
    static std::mutex SPECS_mutex;

    static const std::string BROWSER_COMPATIBILITY;
    static const std::string NETSCAPE;
    static const std::string RFC_2109;
    static const std::string RFC_2965;
    static const std::string IGNORE_COOKIES;
    static const std::string DEFAULT;

    static const int COMPATIBILITY = 0;
    static const int NETSCAPE_DRAFT = 1;
    static const int RFC2109 = 2;
    static const int RFC2965 = 3;

    static int defaultPolicy;

    static Log* LOG;

public:
    static void registerCookieSpec(const std::string& id, std::shared_ptr<CookieSpec> spec) {
        if (id.empty()) {
            throw std::invalid_argument("Id may not be null");
        }
        if (!spec) {
            throw std::invalid_argument("Cookie spec class may not be null");
        }
        std::lock_guard<std::mutex> lock(SPECS_mutex);
        SPECS[id] = spec;
    }

    static void unregisterCookieSpec(const std::string& id) {
        if (id.empty()) {
            throw std::invalid_argument("Id may not be null");
        }
        std::lock_guard<std::mutex> lock(SPECS_mutex);
        SPECS.erase(id);
    }

    static std::shared_ptr<CookieSpec> getCookieSpec(const std::string& id) {
        if (id.empty()) {
            throw std::invalid_argument("Id may not be null");
        }
        std::lock_guard<std::mutex> lock(SPECS_mutex);
        auto it = SPECS.find(id);
        if (it != SPECS.end()) {
            return it->second;
        } else {
            throw std::runtime_error("Unsupported cookie spec " + id);
        }
    }

    static int getDefaultPolicy() {
        return defaultPolicy;
    }

    static void setDefaultPolicy(int policy) {
        defaultPolicy = policy;
    }

    static std::shared_ptr<CookieSpec> getSpecByPolicy(int policy) {
        switch (policy) {
            case COMPATIBILITY:
                return std::make_shared<CookieSpecBase>();
            case NETSCAPE_DRAFT:
                return std::make_shared<NetscapeDraftSpec>();
            case RFC2109:
                return std::make_shared<RFC2109Spec>();
            case RFC2965:
                return std::make_shared<RFC2965Spec>();
            default:
                return getDefaultSpec();
        }
    }

    static std::shared_ptr<CookieSpec> getDefaultSpec() {
        try {
            return getCookieSpec(DEFAULT);
        } catch (const std::runtime_error& e) {
            LOG->warn("Default cookie policy is not registered");
            return std::make_shared<RFC2109Spec>();
        }
    }

    static std::shared_ptr<CookieSpec> getSpecByVersion(int ver) {
        switch (ver) {
            case 0:
                return std::make_shared<NetscapeDraftSpec>();
            case 1:
                return std::make_shared<RFC2109Spec>();
            default:
                return getDefaultSpec();
        }
    }

    static std::shared_ptr<CookieSpec> getCompatibilitySpec() {
        return getSpecByPolicy(COMPATIBILITY);
    }

    static std::vector<std::string> getRegisteredCookieSpecs() {
        std::lock_guard<std::mutex> lock(SPECS_mutex);
        std::vector<std::string> specs;
        for (const auto& pair : SPECS) {
            specs.push_back(pair.first);
        }
        return specs;
    }

    static void initialize() {
        registerCookieSpec(DEFAULT, std::make_shared<RFC2109Spec>());
        registerCookieSpec(RFC_2109, std::make_shared<RFC2109Spec>());
        registerCookieSpec(RFC_2965, std::make_shared<RFC2965Spec>());
        registerCookieSpec(BROWSER_COMPATIBILITY, std::make_shared<CookieSpecBase>());
        registerCookieSpec(NETSCAPE, std::make_shared<NetscapeDraftSpec>());
        registerCookieSpec(IGNORE_COOKIES, std::make_shared<IgnoreCookiesSpec>());
    }
};

std::map<std::string, std::shared_ptr<CookieSpec>> CookiePolicy::SPECS;
std::mutex CookiePolicy::SPECS_mutex;

const std::string CookiePolicy::BROWSER_COMPATIBILITY = "compatibility";
const std::string CookiePolicy::NETSCAPE = "netscape";
const std::string CookiePolicy::RFC_2109 = "rfc2109";
const std::string CookiePolicy::RFC_2965 = "rfc2965";
const std::string CookiePolicy::IGNORE_COOKIES = "ignoreCookies";
const std::string CookiePolicy::DEFAULT = "default";

int CookiePolicy::defaultPolicy = CookiePolicy::RFC2109;
Log* CookiePolicy::LOG = LogFactory::getLog("CookiePolicy");

// ��ʼ����̬��Ա
struct CookiePolicyInitializer {
    CookiePolicyInitializer() {
        CookiePolicy::initialize();
    }
};

static CookiePolicyInitializer initializer;
// ```

// ### ˵����
// 1. **������**������C++���Ѿ�ʵ��������Java��`Map`��`Log`��`LogFactory`����ͽӿڡ�
// 2. **�̰߳�ȫ**��ʹ��`std::mutex`����֤`SPECS`���̰߳�ȫ��
// 3. **��̬��Ա��ʼ��**��ʹ��`CookiePolicyInitializer`�ṹ����ȷ����̬��Ա�ڳ�������ʱ����ʼ����
// 4. **�쳣����**����C++�У��쳣������Java���ƣ�����Ҫ�ֶ��׳��Ͳ����쳣��
// 5. **����ָ��**��ʹ��`std::shared_ptr`������`CookieSpec`������������ڡ�

// ���C++�����Ƕ�Java�����ֱ�ӷ��룬���������б�Ҫ���������Ѿ�ʵ�֡�