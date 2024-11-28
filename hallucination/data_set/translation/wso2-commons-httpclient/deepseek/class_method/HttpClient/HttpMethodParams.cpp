以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，并且C++中已经存在相应的类和函数。

```cpp
#include <string>
#include <vector>
#include <stdexcept>
#include <iostream>
#include <memory>
#include <unordered_map>
#include <utility>

// 假设已经实现了以下依赖项
class HttpVersion;
class CookiePolicy;
class Log;
class LogFactory;
class DefaultHttpParams;
class HttpMethodRetryHandler;

class HttpMethodParams : public DefaultHttpParams {
public:
    // 日志对象
    static std::shared_ptr<Log> LOG;

    // 定义常量字符串
    static const std::string USER_AGENT;
    static const std::string PROTOCOL_VERSION;
    static const std::string UNAMBIGUOUS_STATUS_LINE;
    static const std::string SINGLE_COOKIE_HEADER;
    static const std::string STRICT_TRANSFER_ENCODING;
    static const std::string REJECT_HEAD_BODY;
    static const std::string HEAD_BODY_CHECK_TIMEOUT;
    static const std::string USE_EXPECT_CONTINUE;
    static const std::string CREDENTIAL_CHARSET;
    static const std::string HTTP_ELEMENT_CHARSET;
    static const std::string HTTP_URI_CHARSET;
    static const std::string HTTP_CONTENT_CHARSET;
    static const std::string COOKIE_POLICY;
    static const std::string WARN_EXTRA_INPUT;
    static const std::string STATUS_LINE_GARBAGE_LIMIT;
    static const std::string SO_TIMEOUT;
    static const std::string DATE_PATTERNS;
    static const std::string RETRY_HANDLER;
    static const std::string BUFFER_WARN_TRIGGER_LIMIT;
    static const std::string VIRTUAL_HOST;
    static const std::string MULTIPART_BOUNDARY;

    // 构造函数
    HttpMethodParams() : DefaultHttpParams(getDefaultParams()) {}
    HttpMethodParams(std::shared_ptr<HttpParams> defaults) : DefaultHttpParams(defaults) {}

    // 获取和设置HTTP元素字符集
    std::string getHttpElementCharset() {
        std::string charset = getParameter<std::string>(HTTP_ELEMENT_CHARSET);
        if (charset.empty()) {
            LOG->warn("HTTP element charset not configured, using US-ASCII");
            charset = "US-ASCII";
        }
        return charset;
    }

    void setHttpElementCharset(const std::string& charset) {
        setParameter(HTTP_ELEMENT_CHARSET, charset);
    }

    // 获取和设置内容字符集
    std::string getContentCharset() {
        std::string charset = getParameter<std::string>(HTTP_CONTENT_CHARSET);
        if (charset.empty()) {
            LOG->warn("Default content charset not configured, using ISO-8859-1");
            charset = "ISO-8859-1";
        }
        return charset;
    }

    void setContentCharset(const std::string& charset) {
        setParameter(HTTP_CONTENT_CHARSET, charset);
    }

    // 获取和设置URI字符集
    std::string getUriCharset() {
        std::string charset = getParameter<std::string>(HTTP_URI_CHARSET);
        if (charset.empty()) {
            charset = "UTF-8";
        }
        return charset;
    }

    void setUriCharset(const std::string& charset) {
        setParameter(HTTP_URI_CHARSET, charset);
    }

    // 获取和设置凭证字符集
    std::string getCredentialCharset() {
        std::string charset = getParameter<std::string>(CREDENTIAL_CHARSET);
        if (charset.empty()) {
            LOG->debug("Credential charset not configured, using HTTP element charset");
            charset = getHttpElementCharset();
        }
        return charset;
    }

    void setCredentialCharset(const std::string& charset) {
        setParameter(CREDENTIAL_CHARSET, charset);
    }

    // 获取和设置HTTP协议版本
    std::shared_ptr<HttpVersion> getVersion() {
        std::shared_ptr<HttpVersion> version = getParameter<std::shared_ptr<HttpVersion>>(PROTOCOL_VERSION);
        if (!version) {
            return std::make_shared<HttpVersion>("HTTP/1.1");
        }
        return version;
    }

    void setVersion(std::shared_ptr<HttpVersion> version) {
        setParameter(PROTOCOL_VERSION, version);
    }

    // 获取和设置Cookie策略
    std::string getCookiePolicy() {
        std::string policy = getParameter<std::string>(COOKIE_POLICY);
        if (policy.empty()) {
            return CookiePolicy::DEFAULT;
        }
        return policy;
    }

    void setCookiePolicy(const std::string& policy) {
        setParameter(COOKIE_POLICY, policy);
    }

    // 获取和设置Socket超时时间
    int getSoTimeout() {
        return getIntParameter(SO_TIMEOUT, 0);
    }

    void setSoTimeout(int timeout) {
        setIntParameter(SO_TIMEOUT, timeout);
    }

    // 获取和设置虚拟主机名
    void setVirtualHost(const std::string& hostname) {
        setParameter(VIRTUAL_HOST, hostname);
    }

    std::string getVirtualHost() {
        return getParameter<std::string>(VIRTUAL_HOST);
    }

    // 设置严格模式和宽松模式
    void makeStrict() {
        setParameters(PROTOCOL_STRICTNESS_PARAMETERS, true);
        setIntParameter(STATUS_LINE_GARBAGE_LIMIT, 0);
    }

    void makeLenient() {
        setParameters(PROTOCOL_STRICTNESS_PARAMETERS, false);
        setIntParameter(STATUS_LINE_GARBAGE_LIMIT, std::numeric_limits<int>::max());
    }

private:
    static const std::vector<std::string> PROTOCOL_STRICTNESS_PARAMETERS;
};

// 初始化静态成员
std::shared_ptr<Log> HttpMethodParams::LOG = LogFactory::getLog("HttpMethodParams");

const std::string HttpMethodParams::USER_AGENT = "http.useragent";
const std::string HttpMethodParams::PROTOCOL_VERSION = "http.protocol.version";
const std::string HttpMethodParams::UNAMBIGUOUS_STATUS_LINE = "http.protocol.unambiguous-statusline";
const std::string HttpMethodParams::SINGLE_COOKIE_HEADER = "http.protocol.single-cookie-header";
const std::string HttpMethodParams::STRICT_TRANSFER_ENCODING = "http.protocol.strict-transfer-encoding";
const std::string HttpMethodParams::REJECT_HEAD_BODY = "http.protocol.reject-head-body";
const std::string HttpMethodParams::HEAD_BODY_CHECK_TIMEOUT = "http.protocol.head-body-timeout";
const std::string HttpMethodParams::USE_EXPECT_CONTINUE = "http.protocol.expect-continue";
const std::string HttpMethodParams::CREDENTIAL_CHARSET = "http.protocol.credential-charset";
const std::string HttpMethodParams::HTTP_ELEMENT_CHARSET = "http.protocol.element-charset";
const std::string HttpMethodParams::HTTP_URI_CHARSET = "http.protocol.uri-charset";
const std::string HttpMethodParams::HTTP_CONTENT_CHARSET = "http.protocol.content-charset";
const std::string HttpMethodParams::COOKIE_POLICY = "http.protocol.cookie-policy";
const std::string HttpMethodParams::WARN_EXTRA_INPUT = "http.protocol.warn-extra-input";
const std::string HttpMethodParams::STATUS_LINE_GARBAGE_LIMIT = "http.protocol.status-line-garbage-limit";
const std::string HttpMethodParams::SO_TIMEOUT = "http.socket.timeout";
const std::string HttpMethodParams::DATE_PATTERNS = "http.dateparser.patterns";
const std::string HttpMethodParams::RETRY_HANDLER = "http.method.retry-handler";
const std::string HttpMethodParams::BUFFER_WARN_TRIGGER_LIMIT = "http.method.response.buffer.warnlimit";
const std::string HttpMethodParams::VIRTUAL_HOST = "http.virtual-host";
const std::string HttpMethodParams::MULTIPART_BOUNDARY = "http.method.multipart.boundary";

const std::vector<std::string> HttpMethodParams::PROTOCOL_STRICTNESS_PARAMETERS = {
    UNAMBIGUOUS_STATUS_LINE,
    SINGLE_COOKIE_HEADER,
    STRICT_TRANSFER_ENCODING,
    REJECT_HEAD_BODY,
    WARN_EXTRA_INPUT
};
```

### 说明：
1. **依赖项**：假设`HttpVersion`、`CookiePolicy`、`Log`、`LogFactory`、`DefaultHttpParams`、`HttpMethodRetryHandler`等类已经在C++中实现。
2. **日志系统**：假设`Log`类有一个`warn`和`debug`方法，用于记录日志。
3. **参数设置和获取**：假设`DefaultHttpParams`类中已经实现了`getParameter`、`setParameter`、`getIntParameter`、`setIntParameter`等方法。
4. **字符串常量**：Java中的`public static final String`在C++中被翻译为`static const std::string`。
5. **构造函数**：C++中的构造函数与Java中的构造函数类似，但需要注意初始化列表的使用。
6. **方法实现**：大部分方法的实现与Java中的实现类似，但需要注意C++中的类型转换和智能指针的使用。

这个C++代码是一个直接的翻译，假设所有依赖项都已经实现。如果某些依赖项在C++中不存在，需要根据实际情况进行调整或实现。