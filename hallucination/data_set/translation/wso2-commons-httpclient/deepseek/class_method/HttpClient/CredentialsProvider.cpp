//�����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֡�


#include <string>

// ����AuthScheme��Credentials���Ѿ�����õ���
class AuthScheme;
class Credentials;

// �Զ����쳣��
class CredentialsNotAvailableException : public std::exception {
public:
    const char* what() const noexcept override {
        return "Credentials not available";
    }
};

/**
 * Credentials provider interface can be used to provide HTTP method with a means to request
 * authentication credentials if no credentials have been given or given credentials are incorrect.
 * 
 * HttpClient makes no provisions to check whether the same credentials have been tried already.
 * It is a responsibility of the custom credentials provider to keep track of authentication attempts
 * and to ensure that credentials known to be invalid are not retried. HttpClient will simply store
 * the set of credentials returned by the custom credentials provider in the http state object and
 * will attempt to use these credentials for all subsequent requests with the given authentication scope.
 * 
 * Classes implementing this interface must synchronize access to shared data as methods of this interface
 * may be executed from multiple threads.
 */
class CredentialsProvider {
public:
    /**
     * Sets the credentials provider parameter.
     * This parameter expects a value of type CredentialsProvider.
     */
    static const std::string PROVIDER;

    /**
     * Requests additional authentication credentials.
     * 
     * @param scheme the authentication scheme
     * @param host the authentication host
     * @param port the port of the authentication host
     * @param proxy true if authenticating with a proxy, false otherwise
     * @return Credentials object containing the requested credentials
     * @throws CredentialsNotAvailableException if credentials are not available
     */
    virtual Credentials getCredentials(
        const AuthScheme& scheme, 
        const std::string& host, 
        int port, 
        bool proxy) = 0;

    virtual ~CredentialsProvider() = default;
};

const std::string CredentialsProvider::PROVIDER = "http.authentication.credential-provider";
// ```

// ### ˵����
// 1. **�ඨ��**����C++�У��ӿ�ͨ��ͨ�����麯����`= 0`����ʵ�֡�`CredentialsProvider`�����һ�����麯��`getCredentials`����ʹ������Ϊһ��������ࡣ
// 2. **�쳣����**����C++�У��쳣����ͨ��ʹ��`std::exception`�������ࡣ���ﶨ����һ��`CredentialsNotAvailableException`������ʾ�޷���ȡƾ֤���쳣�����
// 3. **��������**��Java�е�`public static final`������C++��ͨ��`static const`��Ա������ʵ�֡�
// 4. **������**������`AuthScheme`��`Credentials`���Ѿ��������ط����岢ʵ�֡�

// ���C++������ԭʼJava����Ĺ��ܺͽṹ����һ�£�������ѭ��C++�ı��ϰ�ߡ�