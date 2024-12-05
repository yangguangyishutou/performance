以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，例如`ProtocolSocketFactory`和`SecureProtocolSocketFactory`类。

```cpp
#include <string>
#include <map>
#include <stdexcept>
#include <mutex>
#include <algorithm>

class ProtocolSocketFactory;
class SecureProtocolSocketFactory;

class Protocol {
public:
    // 注册协议
    static void registerProtocol(const std::string& id, Protocol* protocol) {
        if (id.empty()) {
            throw std::invalid_argument("id is null");
        }
        if (protocol == nullptr) {
            throw std::invalid_argument("protocol is null");
        }

        std::lock_guard<std::mutex> lock(protocolsMutex);
        PROTOCOLS[id] = protocol;
    }

    // 取消注册协议
    static void unregisterProtocol(const std::string& id) {
        if (id.empty()) {
            throw std::invalid_argument("id is null");
        }

        std::lock_guard<std::mutex> lock(protocolsMutex);
        PROTOCOLS.erase(id);
    }

    // 获取协议
    static Protocol* getProtocol(const std::string& id) {
        if (id.empty()) {
            throw std::invalid_argument("id is null");
        }

        std::lock_guard<std::mutex> lock(protocolsMutex);
        auto it = PROTOCOLS.find(id);
        if (it != PROTOCOLS.end()) {
            return it->second;
        }

        return lazyRegisterProtocol(id);
    }

    // 构造函数
    Protocol(const std::string& scheme, ProtocolSocketFactory* factory, int defaultPort)
        : scheme(scheme), socketFactory(factory), defaultPort(defaultPort), secure(dynamic_cast<SecureProtocolSocketFactory*>(factory) != nullptr) {
        if (scheme.empty()) {
            throw std::invalid_argument("scheme is null");
        }
        if (factory == nullptr) {
            throw std::invalid_argument("socketFactory is null");
        }
        if (defaultPort <= 0) {
            throw std::invalid_argument("port is invalid: " + std::to_string(defaultPort));
        }
    }

    // 获取默认端口
    int getDefaultPort() const {
        return defaultPort;
    }

    // 获取Socket工厂
    ProtocolSocketFactory* getSocketFactory() const {
        return socketFactory;
    }

    // 获取协议方案
    std::string getScheme() const {
        return scheme;
    }

    // 判断是否为安全协议
    bool isSecure() const {
        return secure;
    }

    // 解析端口
    int resolvePort(int port) const {
        return port <= 0 ? defaultPort : port;
    }

    // 字符串表示
    std::string toString() const {
        return scheme + ":" + std::to_string(defaultPort);
    }

    // 判断是否相等
    bool equals(const Protocol* obj) const {
        if (obj == nullptr) return false;

        return (defaultPort == obj->getDefaultPort() &&
                scheme == obj->getScheme() &&
                secure == obj->isSecure() &&
                socketFactory == obj->getSocketFactory());
    }

    // 获取哈希码
    int hashCode() const {
        int hash = 17;
        hash = 31 * hash + defaultPort;
        hash = 31 * hash + std::hash<std::string>{}(scheme);
        hash = 31 * hash + (secure ? 1 : 0);
        hash = 31 * hash + std::hash<ProtocolSocketFactory*>{}(socketFactory);
        return hash;
    }

private:
    static std::map<std::string, Protocol*> PROTOCOLS;
    static std::mutex protocolsMutex;

    std::string scheme;
    ProtocolSocketFactory* socketFactory;
    int defaultPort;
    bool secure;

    // 懒注册协议
    static Protocol* lazyRegisterProtocol(const std::string& id) {
        if (id == "http") {
            Protocol* http = new Protocol("http", DefaultProtocolSocketFactory::getSocketFactory(), 80);
            registerProtocol("http", http);
            return http;
        }

        if (id == "https") {
            Protocol* https = new Protocol("https", SSLProtocolSocketFactory::getSocketFactory(), 443);
            registerProtocol("https", https);
            return https;
        }

        throw std::invalid_argument("unsupported protocol: '" + id + "'");
    }
};

std::map<std::string, Protocol*> Protocol::PROTOCOLS;
std::mutex Protocol::protocolsMutex;
```

### 说明：
1. **线程安全**：Java中的`Collections.synchronizedMap`在C++中通过`std::mutex`实现。
2. **动态类型检查**：Java中的`instanceof`在C++中通过`dynamic_cast`实现。
3. **哈希码**：Java中的`hashCode`方法在C++中通过简单的哈希函数实现。
4. **内存管理**：C++中需要手动管理内存，因此在使用`new`创建对象时，需要确保在适当的时候使用`delete`释放内存。

### 依赖项：
- `ProtocolSocketFactory` 和 `SecureProtocolSocketFactory` 类需要已经实现。
- `DefaultProtocolSocketFactory` 和 `SSLProtocolSocketFactory` 类需要已经实现，并且有`getSocketFactory`静态方法。