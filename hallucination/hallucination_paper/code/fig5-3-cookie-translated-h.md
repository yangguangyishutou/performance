
```cpp
#ifndef COOKIE_H
#define COOKIE_H

#include <string>
#include <vector>
#include <functional>

class Cookie {
private:
    std::string name;
    std::string value;
    std::vector<std::string> attributes;

public:
    Cookie(const std::string& name, const std::string& value);

    const std::string& getName() const;
    void addAttribute(const std::string& attr);
    std::vector<std::string> getAttributes() const;

    bool operator==(const Cookie& other) const;
    bool operator!=(const Cookie& other) const;

    std::size_t hashCode() const;
};

namespace std {
    template<>
    struct hash<Cookie> {
        std::size_t operator()(const Cookie& cookie) const {
            return cookie.hashCode();
        }
    };
}

#endif // COOKIE_H
```