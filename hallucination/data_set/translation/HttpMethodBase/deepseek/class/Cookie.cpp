以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，并且C++中已经实现了类似的类和函数。

```cpp
#include <string>
#include <ctime>
#include <stdexcept>
#include <algorithm>
#include <iostream>
#include <memory>

// 假设已经实现了以下类和函数
class CookieSpec;
class CookiePolicy;
class LangUtils;
class Log;
class LogFactory;

class Cookie : public NameValuePair, public Comparator {
public:
    // ----------------------------------------------------------- Constructors

    /**
     * Default constructor. Creates a blank cookie 
     */
    Cookie() : Cookie(nullptr, "noname", nullptr, nullptr, nullptr, false) {}

    /**
     * Creates a cookie with the given name, value and domain attribute.
     *
     * @param name    the cookie name
     * @param value   the cookie value
     * @param domain  the domain this cookie can be sent to
     */
    Cookie(const std::string& domain, const std::string& name, const std::string& value)
        : Cookie(domain, name, value, nullptr, nullptr, false) {}

    /**
     * Creates a cookie with the given name, value, domain attribute,
     * path attribute, expiration attribute, and secure attribute 
     *
     * @param name    the cookie name
     * @param value   the cookie value
     * @param domain  the domain this cookie can be sent to
     * @param path    the path prefix for which this cookie can be sent
     * @param expires the {@link Date} at which this cookie expires,
     *                or <tt>null</tt> if the cookie expires at the end
     *                of the session
     * @param secure if true this cookie can only be sent over secure
     * connections
     * @throws IllegalArgumentException If cookie name is null or blank,
     *   cookie name contains a blank, or cookie name starts with character $
     *   
     */
    Cookie(const std::string& domain, const std::string& name, const std::string& value, 
           const std::string& path, const std::time_t* expires, bool secure)
        : NameValuePair(name, value) {
        LOG->trace("enter Cookie(String, String, String, String, Date, boolean)");
        if (name.empty()) {
            throw std::invalid_argument("Cookie name may not be null");
        }
        if (name.find_first_not_of(' ') == std::string::npos) {
            throw std::invalid_argument("Cookie name may not be blank");
        }
        setPath(path);
        setDomain(domain);
        setExpiryDate(expires);
        setSecure(secure);
    }

    /**
     * Creates a cookie with the given name, value, domain attribute,
     * path attribute, maximum age attribute, and secure attribute 
     *
     * @param name   the cookie name
     * @param value  the cookie value
     * @param domain the domain this cookie can be sent to
     * @param path   the path prefix for which this cookie can be sent
     * @param maxAge the number of seconds for which this cookie is valid.
     *               maxAge is expected to be a non-negative number. 
     *               <tt>-1</tt> signifies that the cookie should never expire.
     * @param secure if <tt>true</tt> this cookie can only be sent over secure
     * connections
     */
    Cookie(const std::string& domain, const std::string& name, const std::string& value, 
           const std::string& path, int maxAge, bool secure)
        : Cookie(domain, name, value, path, nullptr, secure) {
        if (maxAge < -1) {
            throw std::invalid_argument("Invalid max age: " + std::to_string(maxAge));
        }            
        if (maxAge >= 0) {
            std::time_t expiryDate = std::time(nullptr) + maxAge;
            setExpiryDate(&expiryDate);
        }
    }

    /**
     * Returns the comment describing the purpose of this cookie, or
     * <tt>null</tt> if no such comment has been defined.
     * 
     * @return comment 
     *
     * @see #setComment(String)
     */
    const std::string& getComment() const {
        return cookieComment;
    }

    /**
     * If a user agent (web browser) presents this cookie to a user, the
     * cookie's purpose will be described using this comment.
     * 
     * @param comment
     *  
     * @see #getComment()
     */
    void setComment(const std::string& comment) {
        cookieComment = comment;
    }

    /**
     * Returns the expiration {@link Date} of the cookie, or <tt>null</tt>
     * if none exists.
     * <p><strong>Note:</strong> the object returned by this method is 
     * considered immutable. Changing it (e.g. using setTime()) could result
     * in undefined behaviour. Do so at your peril. </p>
     * @return Expiration {@link Date}, or <tt>null</tt>.
     *
     * @see #setExpiryDate(java.util.Date)
     *
     */
    const std::time_t* getExpiryDate() const {
        return cookieExpiryDate;
    }

    /**
     * Sets expiration date.
     * <p><strong>Note:</strong> the object returned by this method is considered
     * immutable. Changing it (e.g. using setTime()) could result in undefined 
     * behaviour. Do so at your peril.</p>
     *
     * @param expiryDate the {@link Date} after which this cookie is no longer valid.
     *
     * @see #getExpiryDate
     *
     */
    void setExpiryDate(const std::time_t* expiryDate) {
        cookieExpiryDate = expiryDate;
    }

    /**
     * Returns <tt>false</tt> if the cookie should be discarded at the end
     * of the "session"; <tt>true</tt> otherwise.
     *
     * @return <tt>false</tt> if the cookie should be discarded at the end
     *         of the "session"; <tt>true</tt> otherwise
     */
    bool isPersistent() const {
        return (cookieExpiryDate != nullptr);
    }

    /**
     * Returns domain attribute of the cookie.
     * 
     * @return the value of the domain attribute
     *
     * @see #setDomain(java.lang.String)
     */
    const std::string& getDomain() const {
        return cookieDomain;
    }

    /**
     * Sets the domain attribute.
     * 
     * @param domain The value of the domain attribute
     *
     * @see #getDomain
     */
    void setDomain(const std::string& domain) {
        if (!domain.empty()) {
            size_t ndx = domain.find(':');
            if (ndx != std::string::npos) {
                cookieDomain = domain.substr(0, ndx);
            } else {
                cookieDomain = domain;
            }
            std::transform(cookieDomain.begin(), cookieDomain.end(), cookieDomain.begin(), ::tolower);
        }
    }

    /**
     * Returns the path attribute of the cookie
     * 
     * @return The value of the path attribute.
     * 
     * @see #setPath(java.lang.String)
     */
    const std::string& getPath() const {
        return cookiePath;
    }

    /**
     * Sets the path attribute.
     *
     * @param path The value of the path attribute
     *
     * @see #getPath
     *
     */
    void setPath(const std::string& path) {
        cookiePath = path;
    }

    /**
     * @return <code>true</code> if this cookie should only be sent over secure connections.
     * @see #setSecure(boolean)
     */
    bool getSecure() const {
        return isSecure;
    }

    /**
     * Sets the secure attribute of the cookie.
     * <p>
     * When <tt>true</tt> the cookie should only be sent
     * using a secure protocol (https).  This should only be set when
     * the cookie's originating server used a secure protocol to set the
     * cookie's value.
     *
     * @param secure The value of the secure attribute
     * 
     * @see #getSecure()
     */
    void setSecure(bool secure) {
        isSecure = secure;
    }

    /**
     * Returns the version of the cookie specification to which this
     * cookie conforms.
     *
     * @return the version of the cookie.
     * 
     * @see #setVersion(int)
     *
     */
    int getVersion() const {
        return cookieVersion;
    }

    /**
     * Sets the version of the cookie specification to which this
     * cookie conforms. 
     *
     * @param version the version of the cookie.
     * 
     * @see #getVersion
     */
    void setVersion(int version) {
        cookieVersion = version;
    }

    /**
     * Returns true if this cookie has expired.
     * 
     * @return <tt>true</tt> if the cookie has expired.
     */
    bool isExpired() const {
        return (cookieExpiryDate != nullptr  
            && *cookieExpiryDate <= std::time(nullptr));
    }

    /**
     * Returns true if this cookie has expired according to the time passed in.
     * 
     * @param now The current time.
     * 
     * @return <tt>true</tt> if the cookie expired.
     */
    bool isExpired(std::time_t now) const {
        return (cookieExpiryDate != nullptr  
            && *cookieExpiryDate <= now);
    }

    /**
     * Indicates whether the cookie had a path specified in a 
     * path attribute of the <tt>Set-Cookie</tt> header. This value
     * is important for generating the <tt>Cookie</tt> header because 
     * some cookie specifications require that the <tt>Cookie</tt> header 
     * should only include a path attribute if the cookie's path 
     * was specified in the <tt>Set-Cookie</tt> header.
     *
     * @param value <tt>true</tt> if the cookie's path was explicitly 
     * set, <tt>false</tt> otherwise.
     * 
     * @see #isPathAttributeSpecified
     */
    void setPathAttributeSpecified(bool value) {
        hasPathAttribute = value;
    }

    /**
     * Returns <tt>true</tt> if cookie's path was set via a path attribute
     * in the <tt>Set-Cookie</tt> header.
     *
     * @return value <tt>true</tt> if the cookie's path was explicitly 
     * set, <tt>false</tt> otherwise.
     * 
     * @see #setPathAttributeSpecified
     */
    bool isPathAttributeSpecified() const {
        return hasPathAttribute;
    }

    /**
     * Indicates whether the cookie had a domain specified in a 
     * domain attribute of the <tt>Set-Cookie</tt> header. This value
     * is important for generating the <tt>Cookie</tt> header because 
     * some cookie specifications require that the <tt>Cookie</tt> header 
     * should only include a domain attribute if the cookie's domain 
     * was specified in the <tt>Set-Cookie</tt> header.
     *
     * @param value <tt>true</tt> if the cookie's domain was explicitly 
     * set, <tt>false</tt> otherwise.
     *
     * @see #isDomainAttributeSpecified
     */
    void setDomainAttributeSpecified(bool value) {
        hasDomainAttribute = value;
    }

    /**
     * Returns <tt>true</tt> if cookie's domain was set via a domain 
     * attribute in the <tt>Set-Cookie</tt> header.
     *
     * @return value <tt>true</tt> if the cookie's domain was explicitly 
     * set, <tt>false</tt> otherwise.
     *
     * @see #setDomainAttributeSpecified
     */
    bool isDomainAttributeSpecified() const {
        return hasDomainAttribute;
    }

    /**
     * Returns a hash code in keeping with the
     * {@link Object#hashCode} general hashCode contract.
     * @return A hash code
     */
    int hashCode() const {
        int hash = LangUtils::HASH_SEED;
        hash = LangUtils::hashCode(hash, getName());
        hash = LangUtils::hashCode(hash, cookieDomain);
        hash = LangUtils::hashCode(hash, cookiePath);
        return hash;
    }

    /**
     * Two cookies are equal if the name, path and domain match.
     * @param obj The object to compare against.
     * @return true if the two objects are equal.
     */
    bool equals(const Cookie& obj) const {
        if (this == &obj) return true;
        return LangUtils::equals(getName(), obj.getName())
              && LangUtils::equals(cookieDomain, obj.cookieDomain)
              && LangUtils::equals(cookiePath, obj.cookiePath);
    }

    /**
     * Return a textual representation of the cookie.
     * 
     * @return string.
     */
    std::string toExternalForm() const {
        std::unique_ptr<CookieSpec> spec;
        if (getVersion() > 0) {
            spec.reset(CookiePolicy::getDefaultSpec()); 
        } else {
            spec.reset(CookiePolicy::getCookieSpec(CookiePolicy::NETSCAPE)); 
        }
        return spec->formatCookie(*this); 
    }

    /**
     * <p>Compares two cookies to determine order for cookie header.</p>
     * <p>Most specific should be first. </p>
     * <p>This method is implemented so a cookie can be used as a comparator for
     * a SortedSet of cookies. Specifically it's used above in the 
     * createCookieHeader method.</p>
     * @param o1 The first object to be compared
     * @param o2 The second object to be compared
     * @return See {@link java.util.Comparator#compare(Object,Object)}
     */
    int compare(const Cookie& c1, const Cookie& c2) const {
        LOG->trace("enter Cookie.compare(Object, Object)");

        if (c1.getPath().empty() && c2.getPath().empty()) {
            return 0;
        } else if (c1.getPath().empty()) {
            // null is assumed to be "/"
            if (c2.getPath() == CookieSpec::PATH_DELIM) {
                return 0;
            } else {
                return -1;
            }
        } else if (c2.getPath().empty()) {
            // null is assumed to be "/"
            if (c1.getPath() == CookieSpec::PATH_DELIM) {
                return 0;
            } else {
                return 1;
            }
        } else {
            return c1.getPath().compare(c2.getPath());
        }
    }

    /**
     * Return a textual representation of the cookie.
     * 
     * @return string.
     * 
     * @see #toExternalForm
     */
    std::string toString() const {
        return toExternalForm();
    }

private:
    // ----------------------------------------------------- Instance Variables

    /** Comment attribute. */
    std::string  cookieComment;

    /** Domain attribute. */
    std::string  cookieDomain;

    /** Expiration {@link Date}. */
    const std::time_t* cookieExpiryDate = nullptr;

    /** Path attribute. */
    std::string  cookiePath;

    /** My secure flag. */
    bool isSecure = false;

    /**
     * Specifies if the set-cookie header included a Path attribute for this
     * cookie
     */
    bool hasPathAttribute = false;

    /**
     * Specifies if the set-cookie header included a Domain attribute for this
     * cookie
     */
    bool hasDomainAttribute = false;

    /** The version of the cookie specification I was created from. */
    int cookieVersion = 0;

    // -------------------------------------------------------------- Constants

    /** Log object for this class */
    static std::unique_ptr<Log> LOG;
};

std::unique_ptr<Log> Cookie::LOG = LogFactory::getLog(typeid(Cookie).name());
```

### 说明：
1. **时间处理**：Java中的`Date`类在C++中没有直接对应的类，因此使用了`std::time_t`来