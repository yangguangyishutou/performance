//�����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����`AuthScheme`���`AuthPolicy`�ࡣ

//```cpp
#include <string>
#include <stdexcept>
#include <sstream>

class AuthScheme {
public:
    virtual std::string getRealm() const = 0;
    virtual std::string getSchemeName() const = 0;
    virtual ~AuthScheme() = default;
};

class AuthPolicy {
public:
    static AuthScheme* getAuthScheme(const std::string& schemeName) {
        // ��������һ����������������һ��AuthSchemeʵ��
        // ������Ҫ����ʵ�ʵ�ʵ����������Ӧ��AuthSchemeʵ��
        // ���磺
        // if (schemeName == "basic") return new BasicAuthScheme();
        // else if (schemeName == "digest") return new DigestAuthScheme();
        // else return nullptr;
        return nullptr;
    }
};

class AuthState {
public:
    static const std::string PREEMPTIVE_AUTH_SCHEME;

private:
    AuthScheme* authScheme = nullptr;
    bool authRequested = false;
    bool authAttempted = false;
    bool preemptive = false;

public:
    AuthState() = default;

    void invalidate() {
        delete authScheme;
        authScheme = nullptr;
        authRequested = false;
        authAttempted = false;
        preemptive = false;
    }

    bool isAuthRequested() const {
        return authRequested;
    }

    void setAuthRequested(bool challengeReceived) {
        authRequested = challengeReceived;
    }

    bool isAuthAttempted() const {
        return authAttempted;
    }

    void setAuthAttempted(bool challengeResponded) {
        authAttempted = challengeResponded;
    }

    void setPreemptive() {
        if (!preemptive) {
            if (authScheme != nullptr) {
                throw std::runtime_error("Authentication state already initialized");
            }
            authScheme = AuthPolicy::getAuthScheme(PREEMPTIVE_AUTH_SCHEME);
            preemptive = true;
        }
    }

    bool isPreemptive() const {
        return preemptive;
    }

    void setAuthScheme(AuthScheme* authScheme) {
        if (authScheme == nullptr) {
            invalidate();
            return;
        }
        if (preemptive && !dynamic_cast<decltype(this->authScheme)>(authScheme)) {
            preemptive = false;
            authAttempted = false;
        }
        delete this->authScheme;
        this->authScheme = authScheme;
    }

    AuthScheme* getAuthScheme() const {
        return authScheme;
    }

    std::string getRealm() const {
        return (authScheme != nullptr) ? authScheme->getRealm() : std::string();
    }

    std::string toString() const {
        std::ostringstream buffer;
        buffer << "Auth state: auth requested [" << authRequested << "]; auth attempted [" << authAttempted;
        if (authScheme != nullptr) {
            buffer << "]; auth scheme [" << authScheme->getSchemeName() << "]; realm [" << authScheme->getRealm();
        }
        buffer << "] preemptive [" << preemptive << "]";
        return buffer.str();
    }

    ~AuthState() {
        delete authScheme;
    }
};

const std::string AuthState::PREEMPTIVE_AUTH_SCHEME = "basic";
// ```

// ### ˵����
// 1. **��ͷ�����ת��**��Java�е���ͷ�����ת��ΪC++�е���ͷ�����
// 2. **��Ա����**��Java�еĳ�Ա������ת��ΪC++�е�˽�г�Ա������
// 3. **���캯������������**��Java�е�Ĭ�Ϲ��캯����ת��ΪC++�е�Ĭ�Ϲ��캯�����������������ͷŶ�̬������ڴ档
// 4. **�ַ�������**��Java�е�`StringBuffer`��ת��ΪC++�е�`std::ostringstream`��
// 5. **�쳣����**��Java�е�`IllegalStateException`��ת��ΪC++�е�`std::runtime_error`��
// 6. **�ڴ����**����C++�У���Ҫ�ֶ������ڴ棬���������`delete`������ͷŶ�̬�����`AuthScheme`����

// ### �����
// - `AuthScheme`����Ҫʵ��`getRealm`��`getSchemeName`������
// - `AuthPolicy`����Ҫʵ��`getAuthScheme`�������÷�������һ��`AuthScheme`ʵ����

// �����ʵ�ʵ��������������е�����ʵ�֡�