以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现。

```cpp
#include <string>
#include <stdexcept>
#include <sstream>
#include <cmath>

class ProtocolException : public std::runtime_error {
public:
    explicit ProtocolException(const std::string& message) : std::runtime_error(message) {}
};

class HttpVersion {
public:
    // 静态常量版本
    static const HttpVersion HTTP_0_9;
    static const HttpVersion HTTP_1_0;
    static const HttpVersion HTTP_1_1;

    // 构造函数
    HttpVersion(int major, int minor) : major(major), minor(minor) {
        if (major < 0) {
            throw std::invalid_argument("HTTP major version number may not be negative");
        }
        if (minor < 0) {
            throw std::invalid_argument("HTTP minor version number may not be negative");
        }
    }

    // 获取主版本号
    int getMajor() const {
        return major;
    }

    // 获取次版本号
    int getMinor() const {
        return minor;
    }

    // 重载等于运算符
    bool operator==(const HttpVersion& other) const {
        return compareTo(other) == 0;
    }

    // 重载不等于运算符
    bool operator!=(const HttpVersion& other) const {
        return compareTo(other) != 0;
    }

    // 重载小于运算符
    bool operator<(const HttpVersion& other) const {
        return compareTo(other) < 0;
    }

    // 重载小于等于运算符
    bool operator<=(const HttpVersion& other) const {
        return compareTo(other) <= 0;
    }

    // 重载大于运算符
    bool operator>(const HttpVersion& other) const {
        return compareTo(other) > 0;
    }

    // 重载大于等于运算符
    bool operator>=(const HttpVersion& other) const {
        return compareTo(other) >= 0;
    }

    // 比较两个版本
    int compareTo(const HttpVersion& other) const {
        if (other.major == major) {
            return minor - other.minor;
        }
        return major - other.major;
    }

    // 转换为字符串
    std::string toString() const {
        std::ostringstream oss;
        oss << "HTTP/" << major << "." << minor;
        return oss.str();
    }

    // 解析HTTP版本字符串
    static HttpVersion parse(const std::string& s) {
        if (s.empty()) {
            throw std::invalid_argument("String may not be null");
        }
        if (s.substr(0, 5) != "HTTP/") {
            throw ProtocolException("Invalid HTTP version string: " + s);
        }

        int major, minor;
        size_t i1 = 5;
        size_t i2 = s.find('.', i1);
        if (i2 == std::string::npos) {
            throw ProtocolException("Invalid HTTP version number: " + s);
        }

        try {
            major = std::stoi(s.substr(i1, i2 - i1));
        } catch (const std::invalid_argument& e) {
            throw ProtocolException("Invalid HTTP major version number: " + s);
        }

        i1 = i2 + 1;
        try {
            minor = std::stoi(s.substr(i1));
        } catch (const std::invalid_argument& e) {
            throw ProtocolException("Invalid HTTP minor version number: " + s);
        }

        return HttpVersion(major, minor);
    }

private:
    int major;
    int minor;
};

// 初始化静态常量
const HttpVersion HttpVersion::HTTP_0_9 = HttpVersion(0, 9);
const HttpVersion HttpVersion::HTTP_1_0 = HttpVersion(1, 0);
const HttpVersion HttpVersion::HTTP_1_1 = HttpVersion(1, 1);
```

### 说明：
1. **异常处理**：Java中的`IllegalArgumentException`和`ProtocolException`在C++中分别用`std::invalid_argument`和自定义的`ProtocolException`类来替代。
2. **字符串处理**：Java中的`StringBuffer`在C++中用`std::ostringstream`来替代。
3. **静态常量**：C++中静态常量的初始化需要在类外部进行。
4. **比较运算符**：C++中重载了比较运算符以便于直接使用`<`, `<=`, `>`, `>=`, `==`, `!=`进行版本比较。

这个C++版本的代码与原始Java代码的功能基本一致，并且遵循了C++的编程风格和习惯。