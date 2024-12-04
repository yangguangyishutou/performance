//�����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����`LangUtils`�ࡣ

#include <string>
#include <cctype>
#include <sstream>
#include <stdexcept>

class AuthScope {
public:
    static const std::string ANY_HOST;
    static const int ANY_PORT = -1;
    static const std::string ANY_REALM;
    static const std::string ANY_SCHEME;
    static const AuthScope ANY;

private:
    std::string scheme;
    std::string realm;
    std::string host;
    int port;

public:
    AuthScope(const std::string& host, int port, const std::string& realm, const std::string& scheme)  //#None#
        : host((host.empty()) ? ANY_HOST : toLowerCase(host)),
          port((port < 0) ? ANY_PORT : port),
          realm((realm.empty()) ? ANY_REALM : realm),
          scheme((scheme.empty()) ? ANY_SCHEME : toUpperCase(scheme)) {}

    AuthScope(const std::string& host, int port, const std::string& realm)  //#None#
        : AuthScope(host, port, realm, ANY_SCHEME) {}

    AuthScope(const std::string& host, int port)
        : AuthScope(host, port, ANY_REALM, ANY_SCHEME) {}

    AuthScope(const AuthScope& authscope) {
        if (authscope.host.empty()) {
            throw std::invalid_argument("Scope may not be null");
        }
        this->host = authscope.host;
        this->port = authscope.port;
        this->realm = authscope.realm;
        this->scheme = authscope.scheme;
    }

    std::string getHost() const {
        return this->host;
    }

    int getPort() const {  //#None#
        return this->port;
    }

    std::string getRealm() const {
        return this->realm;
    }

    std::string getScheme() const {
        return this->scheme;
    }

    static bool paramsEqual(const std::string& p1, const std::string& p2) {
        if (p1.empty()) {
            return p1 == p2;
        } else {
            return p1 == p2;
        }
    }

    static bool paramsEqual(int p1, int p2) {
        return p1 == p2;
    }

    int match(const AuthScope& that) const {
        int factor = 0;
        if (paramsEqual(this->scheme, that.scheme)) {
            factor += 1;
        } else {
            if (this->scheme != ANY_SCHEME && that.scheme != ANY_SCHEME) {
                return -1;
            }
        }
        if (paramsEqual(this->realm, that.realm)) {
            factor += 2;
        } else {
            if (this->realm != ANY_REALM && that.realm != ANY_REALM) {
                return -1;
            }
        }
        if (paramsEqual(this->port, that.port)) {
            factor += 4;
        } else {
            if (this->port != ANY_PORT && that.port != ANY_PORT) {
                return -1;
            }
        }
        if (paramsEqual(this->host, that.host)) {
            factor += 8;
        } else {
            if (this->host != ANY_HOST && that.host != ANY_HOST) {
                return -1;
            }
        }
        return factor;
    }

    bool operator==(const AuthScope& other) const {
        if (&other == this) {
            return true;
        }
        return paramsEqual(this->host, other.host) &&
               paramsEqual(this->port, other.port) &&
               paramsEqual(this->realm, other.realm) &&
               paramsEqual(this->scheme, other.scheme);
    }

    bool operator!=(const AuthScope& other) const {
        return !(*this == other);
    }

    std::string toString() const {
        std::ostringstream buffer;
        if (!this->scheme.empty()) {
            buffer << toUpperCase(this->scheme) << " ";
        }
        if (!this->realm.empty()) {
            buffer << "'" << this->realm << "'";
        } else {
            buffer << "<any realm>";
        }
        if (!this->host.empty()) {
            buffer << "@" << this->host;
            if (this->port >= 0) {
                buffer << ":" << this->port;
            }
        }
        return buffer.str();
    }

    int hashCode() const {
        int hash = LangUtils::HASH_SEED;
        hash = LangUtils::hashCode(hash, this->host);
        hash = LangUtils::hashCode(hash, this->port);
        hash = LangUtils::hashCode(hash, this->realm);
        hash = LangUtils::hashCode(hash, this->scheme);
        return hash;
    }

private:
    static std::string toLowerCase(const std::string& str) {
        std::string result = str;
        for (char& c : result) {
            c = std::tolower(c);
        }
        return result;
    }

    static std::string toUpperCase(const std::string& str) {
        std::string result = str;
        for (char& c : result) {
            c = std::toupper(c);
        }
        return result;
    }
};

const std::string AuthScope::ANY_HOST = "";
const std::string AuthScope::ANY_REALM = "";
const std::string AuthScope::ANY_SCHEME = "";
const AuthScope AuthScope::ANY = AuthScope(ANY_HOST, ANY_PORT, ANY_REALM, ANY_SCHEME);
// ```

// ### ˵����
// 1. **�ַ�������**��Java�е�`null`��C++���ÿ��ַ���`""`��ʾ��
// 2. **��Сдת��**��Java�е�`toLowerCase`��`toUpperCase`������C++��ͨ��`std::tolower`��`std::toupper`ʵ�֡�
// 3. **��̬��Ա��ʼ��**��C++�о�̬��Ա��Ҫ��������г�ʼ����
// 4. **�쳣����**��Java�е�`IllegalArgumentException`��C++����`std::invalid_argument`��ʾ��
// 5. **�ַ���ƴ��**��Java�е�`StringBuffer`��C++����`std::ostringstream`ʵ�֡�

// ���C++�汾�Ĵ�����ԭʼJava����Ĺ��ܻ���һ�£�����Ҫע��C++�е��ַ����������쳣������ʽ��Java������ͬ��