//�����ǽ�������Java�ӿ� `AuthScheme` �����C++�Ĵ��롣������ص�������� `Credentials` �� `HttpMethod`���Ѿ�ʵ�֡�


#include <string>
#include <stdexcept>

// ������Щ�������Ѿ�ʵ��
class Credentials;
class HttpMethod;

// �����쳣��
class MalformedChallengeException : public std::runtime_error {
public:
    explicit MalformedChallengeException(const std::string& message)
        : std::runtime_error(message) {}
};

class AuthenticationException : public std::runtime_error {
public:
    explicit AuthenticationException(const std::string& message)
        : std::runtime_error(message) {}
};

// AuthScheme �ӿ�
class AuthScheme {
public:
    virtual ~AuthScheme() = default;

    /**
     * Processes the given challenge token. Some authentication schemes
     * may involve multiple challenge-response exchanges. Such schemes must be able 
     * to maintain the state information when dealing with sequential challenges 
     * 
     * @param challenge the challenge string
     * 
     * @throws MalformedChallengeException if the challenge is malformed
     */
    virtual void processChallenge(const std::string& challenge) = 0;
    
    /**
     * Returns textual designation of the given authentication scheme.
     * 
     * @return the name of the given authentication scheme
     */
    virtual std::string getSchemeName() const = 0;

    /**
     * Returns authentication parameter with the given name, if available.
     * 
     * @param name The name of the parameter to be returned
     * 
     * @return the parameter with the given name, or an empty string if not found
     */
    virtual std::string getParameter(const std::string& name) const = 0;

    /**
     * Returns authentication realm. If the concept of an authentication
     * realm is not applicable to the given authentication scheme, returns
     * an empty string.
     * 
     * @return the authentication realm, or an empty string if not applicable
     */
    virtual std::string getRealm() const = 0;
    
    /**
     * Returns a String identifying the authentication challenge.  This is
     * used, in combination with the host and port to determine if
     * authorization has already been attempted or not.  Schemes which
     * require multiple requests to complete the authentication should
     * return a different value for each stage in the request.
     * 
     * <p>Additionally, the ID should take into account any changes to the
     * authentication challenge and return a different value when appropriate.
     * For example when the realm changes in basic authentication it should be
     * considered a different authentication attempt and a different value should
     * be returned.</p>
     * 
     * @return String a String identifying the authentication challenge.  The
     * returned value may be an empty string.
     * 
     * @deprecated no longer used
     */
    virtual std::string getID() const = 0;

    /**
     * Tests if the authentication scheme is provides authorization on a per
     * connection basis instead of usual per request basis
     * 
     * @return true if the scheme is connection based, false
     * if the scheme is request based.
     */
    virtual bool isConnectionBased() const = 0;    
    
    /**
     * Authentication process may involve a series of challenge-response exchanges.
     * This method tests if the authorization process has been completed, either
     * successfully or unsuccessfully, that is, all the required authorization 
     * challenges have been processed in their entirety.
     * 
     * @return true if the authentication process has been completed, 
     * false otherwise.
     */
    virtual bool isComplete() const = 0;    
    
    /**
     * @deprecated Use authenticate(Credentials, HttpMethod)
     * 
     * Produces an authorization string for the given set of {@link Credentials},
     * method name and URI using the given authentication scheme in response to 
     * the actual authorization challenge.
     * 
     * @param credentials The set of credentials to be used for athentication
     * @param method The name of the method that requires authorization. 
     *   This parameter may be ignored, if it is irrelevant 
     *   or not applicable to the given authentication scheme
     * @param uri The URI for which authorization is needed. 
     *   This parameter may be ignored, if it is irrelevant or not 
     *   applicable to the given authentication scheme
     * @throws AuthenticationException if authorization string cannot 
     *   be generated due to an authentication failure
     * 
     * @return the authorization string
     */
    virtual std::string authenticate(const Credentials& credentials, const std::string& method, const std::string& uri) = 0;

    /**
     * Produces an authorization string for the given set of {@link Credentials}.
     * 
     * @param credentials The set of credentials to be used for athentication
     * @param method The method being authenticated
     * @throws AuthenticationException if authorization string cannot 
     *   be generated due to an authentication failure
     * 
     * @return the authorization string
     */
    virtual std::string authenticate(const Credentials& credentials, const HttpMethod& method) = 0;
};


// ### ˵����
// 1. **�쳣����**����C++�У��쳣����ͨ��ʹ�ñ�׼���е� `std::runtime_error` ������������ʵ�֡����ﶨ���� `MalformedChallengeException` �� `AuthenticationException` �����쳣�ࡣ
// 2. **�ӿڶ���**��C++��û��ֱ�ӵĽӿڸ��������ͨ�����麯����`= 0`��������һ��������࣬������Java�еĽӿڡ�
// 3. **����ֵ����**����C++�У�����������ܷ��ؿ�ֵ��ͨ������һ�����ַ�����`std::string`�������� `nullptr`��
// 4. **������**������ `Credentials` �� `HttpMethod` ���Ѿ�ʵ�֣����ڴ�����ʹ�á�

// ���C++����ʵ������Java�ӿ� `AuthScheme` ��ͬ�Ĺ��ܣ�������ѭ��C++�ı��ϰ�ߡ�