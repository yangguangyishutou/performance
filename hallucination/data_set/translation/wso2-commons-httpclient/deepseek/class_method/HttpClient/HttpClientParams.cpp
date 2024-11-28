//�����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����C++�е���ͺ�����Java�е���ͺ���������ͬ�Ĺ��ܡ�


#include <string>
#include <unordered_map>
#include <stdexcept>

class HttpParams {
public:
    virtual ~HttpParams() = default;
    virtual long getLongParameter(const std::string& name, long defaultValue) const = 0;
    virtual void setLongParameter(const std::string& name, long value) = 0;
    virtual bool getBooleanParameter(const std::string& name, bool defaultValue) const = 0;
    virtual void setBooleanParameter(const std::string& name, bool value) = 0;
    virtual void* getParameter(const std::string& name) const = 0;
    virtual void setParameter(const std::string& name, void* value) = 0;
    virtual void setParameters(const std::string* names, bool value) = 0;
    virtual void makeStrict() = 0;
    virtual void makeLenient() = 0;
};

class HttpMethodParams : public HttpParams {
public:
    HttpMethodParams() = default;
    HttpMethodParams(HttpParams* defaults) : defaults(defaults) {}

    long getLongParameter(const std::string& name, long defaultValue) const override {
        auto it = longParams.find(name);
        if (it != longParams.end()) {
            return it->second;
        }
        if (defaults) {
            return defaults->getLongParameter(name, defaultValue);
        }
        return defaultValue;
    }

    void setLongParameter(const std::string& name, long value) override {
        longParams[name] = value;
    }

    bool getBooleanParameter(const std::string& name, bool defaultValue) const override {
        auto it = boolParams.find(name);
        if (it != boolParams.end()) {
            return it->second;
        }
        if (defaults) {
            return defaults->getBooleanParameter(name, defaultValue);
        }
        return defaultValue;
    }

    void setBooleanParameter(const std::string& name, bool value) override {
        boolParams[name] = value;
    }

    void* getParameter(const std::string& name) const override {
        auto it = params.find(name);
        if (it != params.end()) {
            return it->second;
        }
        if (defaults) {
            return defaults->getParameter(name);
        }
        return nullptr;
    }

    void setParameter(const std::string& name, void* value) override {
        params[name] = value;
    }

    void setParameters(const std::string* names, bool value) override {
        for (int i = 0; !names[i].empty(); ++i) {
            setBooleanParameter(names[i], value);
        }
    }

    void makeStrict() override {
        // Implementation of makeStrict
    }

    void makeLenient() override {
        // Implementation of makeLenient
    }

private:
    HttpParams* defaults = nullptr;
    std::unordered_map<std::string, long> longParams;
    std::unordered_map<std::string, bool> boolParams;
    std::unordered_map<std::string, void*> params;
};

class HttpClientParams : public HttpMethodParams {
public:
    static const std::string CONNECTION_MANAGER_TIMEOUT;
    static const std::string CONNECTION_MANAGER_CLASS;
    static const std::string PREEMPTIVE_AUTHENTICATION;
    static const std::string REJECT_RELATIVE_REDIRECT;
    static const std::string MAX_REDIRECTS;
    static const std::string ALLOW_CIRCULAR_REDIRECTS;

    HttpClientParams() = default;
    HttpClientParams(HttpParams* defaults) : HttpMethodParams(defaults) {}

    long getConnectionManagerTimeout() const {
        return getLongParameter(CONNECTION_MANAGER_TIMEOUT, 0);
    }

    void setConnectionManagerTimeout(long timeout) {
        setLongParameter(CONNECTION_MANAGER_TIMEOUT, timeout);
    }

    void* getConnectionManagerClass() const {
        return getParameter(CONNECTION_MANAGER_CLASS);
    }

    void setConnectionManagerClass(void* clazz) {
        setParameter(CONNECTION_MANAGER_CLASS, clazz);
    }

    bool isAuthenticationPreemptive() const {
        return getBooleanParameter(PREEMPTIVE_AUTHENTICATION, false);
    }

    void setAuthenticationPreemptive(bool value) {
        setBooleanParameter(PREEMPTIVE_AUTHENTICATION, value);
    }

    void makeStrict() override {
        HttpMethodParams::makeStrict();
        const std::string strictParams[] = {
            REJECT_RELATIVE_REDIRECT,
            ALLOW_CIRCULAR_REDIRECTS,
            ""
        };
        setParameters(strictParams, true);
    }

    void makeLenient() override {
        HttpMethodParams::makeLenient();
        const std::string lenientParams[] = {
            REJECT_RELATIVE_REDIRECT,
            ALLOW_CIRCULAR_REDIRECTS,
            ""
        };
        setParameters(lenientParams, false);
    }
};

const std::string HttpClientParams::CONNECTION_MANAGER_TIMEOUT = "http.connection-manager.timeout";
const std::string HttpClientParams::CONNECTION_MANAGER_CLASS = "http.connection-manager.class";
const std::string HttpClientParams::PREEMPTIVE_AUTHENTICATION = "http.authentication.preemptive";
const std::string HttpClientParams::REJECT_RELATIVE_REDIRECT = "http.protocol.reject-relative-redirect";
const std::string HttpClientParams::MAX_REDIRECTS = "http.protocol.max-redirects";
const std::string HttpClientParams::ALLOW_CIRCULAR_REDIRECTS = "http.protocol.allow-circular-redirects";
// ```

// ### ˵����
// 1. **��ͷ���������**��C++�е���ͷ�������������Java��һ�£���ʹ����C++�������淶�����磬ʹ��`std::string`����`String`����
// 2. **������**������`HttpParams`��`HttpMethodParams`�����Ѿ�ʵ�֣����Ҿ�����Java����ͬ�Ĺ��ܡ�
// 3. **�����洢**��ʹ��`std::unordered_map`���洢������������Java�е�`Map`��
// 4. **����ת��**��Java�е�`Class`������C++�б��滻Ϊ`void*`����ΪC++��û��ֱ�Ӷ�Ӧ`Class`�����͡�
// 5. **���鴦��**��C++��ʹ��`const std::string[]`����ʾ�ַ������飬��������ĩβ����һ�����ַ�����Ϊ������ǡ�

// ���C++����Ӧ���ܹ�ʵ����ԭʼJava������ͬ�Ĺ��ܡ�