#include <string>
#include <vector>
#include <stdexcept>
#include <memory>
#include <algorithm>

// 假设这些类已经定义
class Cookie;
class Header;
class NameValuePair;
class MalformedCookieException : public std::exception {
    // 自定义异常类的实现
};

/**
 * Defines the cookie management specification.
 * <p>Cookie management specification must define
 * <ul>
 *   <li> rules of parsing "Set-Cookie" header
 *   <li> rules of validation of parsed cookies
 *   <li>  formatting of "Cookie" header 
 * </ul>
 * for a given host, port and path of origin
 */
class CookieSpec {
public:
    /** Path delimiter */
    static const std::string PATH_DELIM;

    /** Path delimiting character */
    static const char PATH_DELIM_CHAR;

    /**
     * Parse the <tt>"Set-Cookie"</tt> header value into Cookie array.
     * 
     * <p>This method will not perform the validation of the resultant
     * {@link Cookie}s</p> 
     *
     * @param host the host which sent the <tt>Set-Cookie</tt> header
     * @param port the port which sent the <tt>Set-Cookie</tt> header
     * @param path the path which sent the <tt>Set-Cookie</tt> header
     * @param secure <tt>true</tt> when the <tt>Set-Cookie</tt> header 
     *  was received over secure connection
     * @param header the <tt>Set-Cookie</tt> received from the server
     * @return a vector of <tt>Cookie</tt>s parsed from the Set-Cookie value
     * @throws MalformedCookieException if an exception occurs during parsing
     * @throws std::invalid_argument if an input parameter is illegal
     */
    virtual std::vector<std::shared_ptr<Cookie>> parse(
        const std::string& host, int port, const std::string& path, bool secure,
        const std::string& header)
        throw(MalformedCookieException, std::invalid_argument) = 0;

    /**
     * Parse the <tt>"Set-Cookie"</tt> Header into an array of Cookies.
     *
     * <p>This method will not perform the validation of the resultant
     * {@link Cookie}s</p> 
     *
     * @param host the host which sent the <tt>Set-Cookie</tt> header
     * @param port the port which sent the <tt>Set-Cookie</tt> header
     * @param path the path which sent the <tt>Set-Cookie</tt> header
     * @param secure <tt>true</tt> when the <tt>Set-Cookie</tt> header 
     *  was received over secure connection
     * @param header the <tt>Set-Cookie</tt> received from the server
     * @return a vector of <tt>Cookie</tt>s parsed from the header
     * @throws MalformedCookieException if an exception occurs during parsing
     * @throws std::invalid_argument if an input parameter is illegal
     */
    virtual std::vector<std::shared_ptr<Cookie>> parse(
        const std::string& host, int port, const std::string& path, bool secure,
        const Header& header)
        throw(MalformedCookieException, std::invalid_argument) = 0;

    /**
     * Parse the cookie attribute and update the corresponding Cookie 
     *  properties.
     *
     * @param attribute cookie attribute from the <tt>Set-Cookie</tt>
     * @param cookie the to be updated
     * @throws MalformedCookieException if an exception occurs during parsing
     * @throws std::invalid_argument if an input parameter is illegal
     */
    virtual void parseAttribute(const NameValuePair& attribute, std::shared_ptr<Cookie> cookie)
        throw(MalformedCookieException, std::invalid_argument) = 0;

    /**
     * Validate the cookie according to validation rules defined by the 
     *  cookie specification.
     *
     * @param host the host from which the {@link Cookie} was received
     * @param port the port from which the {@link Cookie} was received
     * @param path the path from which the {@link Cookie} was received
     * @param secure <tt>true</tt> when the {@link Cookie} was received 
     *  using a secure connection
     * @param cookie the Cookie to validate
     * @throws MalformedCookieException if the cookie is invalid
     * @throws std::invalid_argument if an input parameter is illegal
     */
    virtual void validate(const std::string& host, int port, const std::string& path, bool secure,
        const std::shared_ptr<Cookie>& cookie)
        throw(MalformedCookieException, std::invalid_argument) = 0;

    /**
     * Sets the collection of date patterns used for parsing. The String patterns must be 
     * compatible with {@link java.text.SimpleDateFormat}.
     *
     * @param datepatterns collection of date patterns
     */
    virtual void setValidDateFormats(const std::vector<std::string>& datepatterns) = 0;

    /**
     * Returns the collection of date patterns used for parsing. The String patterns are compatible 
     * with the {@link java.text.SimpleDateFormat}.
     *
     * @return collection of date patterns
     */
    virtual std::vector<std::string> getValidDateFormats() const = 0;

    /**
     * Determines if a Cookie matches a location.
     *
     * @param host the host to which the request is being submitted
     * @param port the port to which the request is being submitted
     * @param path the path to which the request is being submitted
     * @param secure <tt>true</tt> if the request is using a secure connection
     * @param cookie the Cookie to be matched
     *
     * @return <tt>true</tt> if the cookie should be submitted with a request 
     *  with given attributes, <tt>false</tt> otherwise.
     */
    virtual bool match(const std::string& host, int port, const std::string& path, bool secure,
        const std::shared_ptr<Cookie>& cookie) const = 0;

    /**
     * Determines which of an array of Cookies matches a location.
     *
     * @param host the host to which the request is being submitted
     * @param port the port to which the request is being submitted 
     *  (currently ignored)
     * @param path the path to which the request is being submitted
     * @param secure <tt>true</tt> if the request is using a secure protocol
     * @param cookies an array of <tt>Cookie</tt>s to be matched
     *
     * @return a vector of <tt>Cookie</tt>s that match the given attributes
     */
    virtual std::vector<std::shared_ptr<Cookie>> match(
        const std::string& host, int port, const std::string& path, bool secure,
        const std::vector<std::shared_ptr<Cookie>>& cookies) const = 0;

    /**
     * Performs domain-match as defined by the cookie specification.
     * @param host The target host.
     * @param domain The cookie domain attribute.
     * @return true if the specified host matches the given domain.
     * 
     * @since 3.0
     */
    virtual bool domainMatch(const std::string& host, const std::string& domain) const = 0;

    /**
     * Performs path-match as defined by the cookie specification.
     * @param path The target path.
     * @param topmostPath The cookie path attribute.
     * @return true if the paths match
     * 
     * @since 3.0
     */
    virtual bool pathMatch(const std::string& path, const std::string& topmostPath) const = 0;

    /**
     * Create a <tt>"Cookie"</tt> header value for an array of cookies.
     *
     * @param cookie the cookie to be formatted as string
     * @return a string suitable for sending in a <tt>"Cookie"</tt> header.
     */
    virtual std::string formatCookie(const std::shared_ptr<Cookie>& cookie) const = 0;

    /**
     * Create a <tt>"Cookie"</tt> header value for an array of cookies.
     *
     * @param cookies the Cookies to be formatted
     * @return a string suitable for sending in a Cookie header.
     * @throws std::invalid_argument if an input parameter is illegal
     */
    virtual std::string formatCookies(const std::vector<std::shared_ptr<Cookie>>& cookies) const
        throw(std::invalid_argument) = 0;

    /**
     * Create a <tt>"Cookie"</tt> Header for an array of Cookies.
     *
     * @param cookies the Cookies format into a Cookie header
     * @return a Header for the given Cookies.
     * @throws std::invalid_argument if an input parameter is illegal
     */
    virtual std::shared_ptr<Header> formatCookieHeader(const std::vector<std::shared_ptr<Cookie>>& cookies) const
        throw(std::invalid_argument) = 0;

    /**
     * Create a <tt>"Cookie"</tt> Header for single Cookie.
     *
     * @param cookie the Cookie format as a <tt>Cookie</tt> header
     * @return a Cookie header.
     * @throws std::invalid_argument if an input parameter is illegal
     */
    virtual std::shared_ptr<Header> formatCookieHeader(const std::shared_ptr<Cookie>& cookie) const
        throw(std::invalid_argument) = 0;

    virtual ~CookieSpec() = default;
};

const std::string CookieSpec::PATH_DELIM = "/";
const char CookieSpec::PATH_DELIM_CHAR = PATH_DELIM[0];

/*
主要变化点：
异常处理：Java中的throws关键字在C++中通过throw关键字和异常类来实现。

数据类型：Java中的String对应C++中的std::string，Java中的Collection对应C++中的std::vector。

智能指针：为了管理动态分配的对象，使用了std::shared_ptr。

纯虚函数：C++中的接口通过纯虚函数实现，即在函数声明后加上= 0。

静态常量：Java中的static final在C++中通过static const实现。

依赖项：
Cookie、Header、NameValuePair、MalformedCookieException等类需要在C++中定义并实现。

std::vector、std::string、std::shared_ptr等标准库组件已经包含在C++标准库中。
*/