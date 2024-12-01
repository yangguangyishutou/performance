#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <ctime>
using namespace std;
class Date {
public:
    time_t time;
    Date(time_t t = time(0)) : time(t) {}
};
class NameValuePair {
public:
    string name;
    string value;
    NameValuePair(string n, string v) : name(n), value(v) {}
};
class Cookie : public NameValuePair {
public:
    Cookie() : NameValuePair("", ""), cookieComment(""), cookieDomain(""), cookiePath(""), isSecure(false), hasPathAttribute(false), hasDomainAttribute(false), cookieVersion(0) {}
    Cookie(string domain, string name, string value) : NameValuePair(name, value), cookieComment(""), cookieDomain(domain), cookiePath(""), isSecure(false), hasPathAttribute(false), hasDomainAttribute(false), cookieVersion(0) {}
    Cookie(string domain, string name, string value, string path, Date expires, bool secure) : NameValuePair(name, value), cookieComment(""), cookieDomain(domain), cookiePath(path), cookieExpiryDate(expires), isSecure(secure), hasPathAttribute(false), hasDomainAttribute(false), cookieVersion(0) {}
    Cookie(string domain, string name, string value, string path, int maxAge, bool secure) : Cookie(domain, name, value, path, Date(time(0) + maxAge * 1000), secure) {}
    string getComment() { return cookieComment; }
    void setComment(string comment) { cookieComment = comment; }
    Date getExpiryDate() { return cookieExpiryDate; }
    void setExpiryDate(Date expiryDate) { cookieExpiryDate = expiryDate; }
    bool isPersistent() { return cookieExpiryDate.time != 0; }
    string getDomain() { return cookieDomain; }
    void setDomain(string domain) {
        if (!domain.empty()) {
            size_t ndx = domain.find(":");
            if (ndx != string::npos) {
                domain = domain.substr(0, ndx);
            }
            cookieDomain = domain;
        }
    }
    string getPath() { return cookiePath; }
    void setPath(string path) { cookiePath = path; }
    bool getSecure() { return isSecure; }
    void setSecure(bool secure) { isSecure = secure; }