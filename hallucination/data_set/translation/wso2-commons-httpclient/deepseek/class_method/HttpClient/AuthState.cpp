//�����ǽ�������Java���뷭���C++�İ汾��������ص��������`AuthScheme`�ࣩ�Ѿ�ʵ�֡�

#include <string>
#include <stdexcept>
#include <sstream>

class AuthScheme; // ���� AuthScheme ���Ѿ�ʵ��

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
        this->authScheme = nullptr;
        this->authRequested = false;
        this->authAttempted = false;
        this->preemptive = false;
    }

    bool isAuthRequested() const {
        return this->authRequested;
    }

    void setAuthRequested(bool challengeReceived) {
        this->authRequested = challengeReceived;
    }

    bool isAuthAttempted() const {
        return this->authAttempted;
    }

    void setAuthAttempted(bool challengeResponded) {
        this->authAttempted = challengeResponded;
    }

    void setPreemptive() {
        if (!this->preemptive) {
            if (this->authScheme != nullptr) {
                throw std::logic_error("Authentication state already initialized");
            }
            this->authScheme = AuthPolicy::getAuthScheme(PREEMPTIVE_AUTH_SCHEME);
            this->preemptive = true;
        }
    }

    bool isPreemptive() const {
        return this->preemptive;
    }

    void setAuthScheme(AuthScheme* authScheme) {
        if (authScheme == nullptr) {
            invalidate();
            return;
        }
        if (this->preemptive && !(this->authScheme->getClass().isInstance(authScheme))) {
            this->preemptive = false;
            this->authAttempted = false;
        }
        this->authScheme = authScheme;
    }

    AuthScheme* getAuthScheme() const {
        return this->authScheme;
    }

    std::string getRealm() const {
        if (this->authScheme != nullptr) {
            return this->authScheme->getRealm();
        } else {
            return "";
        }
    }

    std::string toString() const {
        std::ostringstream buffer;
        buffer << "Auth state: auth requested [" << this->authRequested << "]; auth attempted [" << this->authAttempted;
        if (this->authScheme != nullptr) {
            buffer << "]; auth scheme [" << this->authScheme->getSchemeName() << "]; realm [" << this->authScheme->getRealm();
        }
        buffer << "] preemptive [" << this->preemptive << "]";
        return buffer.str();
    }
};

const std::string AuthState::PREEMPTIVE_AUTH_SCHEME = "basic";
// ```

// ### ˵����
// 1. **�ඨ��**��`AuthState` �౻����Ϊһ��C++�࣬����˽�г�Ա�����͹�����Ա������
// 2. **��̬����**��`PREEMPTIVE_AUTH_SCHEME` ������Ϊ��ľ�̬������
// 3. **��Ա����**������Java�еķ�������ת��ΪC++�еĳ�Ա���������ұ�������ͬ�Ĺ��ܡ�
// 4. **�쳣����**��Java�е� `IllegalStateException` ��ת��ΪC++�е� `std::logic_error`��
// 5. **�ַ�������**��Java�е� `StringBuffer` ��ת��ΪC++�е� `std::ostringstream` �������ַ�����

// ### �����
// - `AuthScheme` ����Ҫ�Ѿ�ʵ�֣����Ұ��� `getRealm()` �� `getSchemeName()` ������
// - `AuthPolicy` ����Ҫ�Ѿ�ʵ�֣����Ұ��� `getAuthScheme(const std::string& schemeName)` ��̬������
// - `getClass().isInstance(obj)` ������Ҫ���滻ΪC++�е����ͼ���߼���������� `AuthScheme` ����һ�� `getClass()` ��������һ��������Ϣ���󣬲�����һ�� `isInstance(AuthScheme* obj)` ������������͡�

// ���C++����Ӧ���ܹ�ʵ����ԭʼJava������ͬ�Ĺ��ܡ�