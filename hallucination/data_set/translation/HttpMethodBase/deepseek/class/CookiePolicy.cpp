以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现。

```cpp
#include <map>
#include <string>
#include <stdexcept>
#include <memory>
#include <algorithm>
#include <mutex>
#include <vector>
#include <iostream>

// 假设LogFactory和Log类已经实现
class LogFactory;
class Log;

// 假设CookieSpec类已经实现
class CookieSpec;

// 假设RFC2109Spec, RFC2965Spec, CookieSpecBase, NetscapeDraftSpec, IgnoreCookiesSpec类已经实现
class RFC2109Spec;
class RFC2965Spec;
class CookieSpecBase;
class NetscapeDraftSpec;
class IgnoreCookiesSpec;

class CookiePolicy {
public:
    static const std::string BROWSER_COMPATIBILITY;
    static const std::string NETSCAPE;
    static const std::string RFC_2109;
    static const std::string RFC_2965;
    static const std::string IGNORE_COOKIES;
    static const std::string DEFAULT;

    static void registerCookieSpec(const std::string& id, const std::shared_ptr<CookieSpec>& spec);
    static void unregisterCookieSpec(const std::string& id);
    static std::shared_ptr<CookieSpec> getCookieSpec(const std::string& id);
    static std::shared_ptr<CookieSpec> getDefaultSpec();
    static std::vector<std::string> getRegisteredCookieSpecs();

private:
    static std::map<std::string, std::shared_ptr<CookieSpec>> SPECS;
    static std::mutex SPECS_mutex;
    static Log* LOG;

    static void initialize();
};

const std::string CookiePolicy::BROWSER_COMPATIBILITY = "compatibility";
const std::string CookiePolicy::NETSCAPE = "netscape";
const std::string CookiePolicy::RFC_2109 = "rfc2109";
const std::string CookiePolicy::RFC_2965 = "rfc2965";
const std::string CookiePolicy::IGNORE_COOKIES = "ignoreCookies";
const std::string CookiePolicy::DEFAULT = "default";

std::map<std::string, std::shared_ptr<CookieSpec>> CookiePolicy::SPECS;
std::mutex CookiePolicy::SPECS_mutex;
Log* CookiePolicy::LOG = LogFactory::getLog("CookiePolicy");

void CookiePolicy::initialize() {
    registerCookieSpec(DEFAULT, std::make_shared<RFC2109Spec>());
    registerCookieSpec(RFC_2109, std::make_shared<RFC2109Spec>());
    registerCookieSpec(RFC_2965, std::make_shared<RFC2965Spec>());
    registerCookieSpec(BROWSER_COMPATIBILITY, std::make_shared<CookieSpecBase>());
    registerCookieSpec(NETSCAPE, std::make_shared<NetscapeDraftSpec>());
    registerCookieSpec(IGNORE_COOKIES, std::make_shared<IgnoreCookiesSpec>());
}

void CookiePolicy::registerCookieSpec(const std::string& id, const std::shared_ptr<CookieSpec>& spec) {
    if (id.empty()) {
        throw std::invalid_argument("Id may not be null");
    }
    if (!spec) {
        throw std::invalid_argument("Cookie spec may not be null");
    }
    std::lock_guard<std::mutex> lock(SPECS_mutex);
    SPECS[id] = spec;
}

void CookiePolicy::unregisterCookieSpec(const std::string& id) {
    if (id.empty()) {
        throw std::invalid_argument("Id may not be null");
    }
    std::lock_guard<std::mutex> lock(SPECS_mutex);
    SPECS.erase(id);
}

std::shared_ptr<CookieSpec> CookiePolicy::getCookieSpec(const std::string& id) {
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

std::shared_ptr<CookieSpec> CookiePolicy::getDefaultSpec() {
    try {
        return getCookieSpec(DEFAULT);
    } catch (const std::runtime_error& e) {
        LOG->warn("Default cookie policy is not registered");
        return std::make_shared<RFC2109Spec>();
    }
}

std::vector<std::string> CookiePolicy::getRegisteredCookieSpecs() {
    std::lock_guard<std::mutex> lock(SPECS_mutex);
    std::vector<std::string> specs;
    for (const auto& pair : SPECS) {
        specs.push_back(pair.first);
    }
    return specs;
}

// 初始化静态成员
class CookiePolicyInitializer {
public:
    CookiePolicyInitializer() {
        CookiePolicy::initialize();
    }
};

static CookiePolicyInitializer initializer;
```

### 说明：
1. **依赖项**：假设`LogFactory`、`Log`、`CookieSpec`及其子类（如`RFC2109Spec`、`RFC2965Spec`等）已经实现。
2. **线程安全**：使用`std::mutex`来确保`SPECS`的线程安全。
3. **初始化**：使用一个静态初始化类`CookiePolicyInitializer`来确保`initialize`方法在程序启动时被调用。
4. **异常处理**：在C++中，使用`std::invalid_argument`和`std::runtime_error`来处理异常情况。
5. **智能指针**：使用`std::shared_ptr`来管理`CookieSpec`对象的生命周期。