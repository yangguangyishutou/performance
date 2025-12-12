
```cpp
#include "Cookie.h"
#include <stdexcept>
#include <algorithm>

Cookie::Cookie(const std::string& name, const std::string& value)
    : name(name), value(value) {
    if (name.empty()) {
        throw std::invalid_argument("Cookie name cannot be null or empty");
    }
}

const std::string& Cookie::getName() const {
    return name;
}

void Cookie::addAttribute(const std::string& attr) {
    if (attr.empty()) {
        throw std::invalid_argument("Attribute cannot be null or empty");
    }
    attributes.push_back(attr);
}

std::vector<std::string> Cookie::getAttributes() const {
    return attributes; // Return copy due to copy constructor
}

bool Cookie::operator==(const Cookie& other) const {
    return name == other.name && value == other.value;
}

bool Cookie::operator!=(const Cookie& other) const {
    return !(*this == other);
}

std::size_t Cookie::hashCode() const {
    std::size_t h1 = std::hash<std::string>{}(name);
    std::size_t h2 = std::hash<std::string>{}(value);
    return h1 ^ (h2 << 1); // Combine hash values
}
```