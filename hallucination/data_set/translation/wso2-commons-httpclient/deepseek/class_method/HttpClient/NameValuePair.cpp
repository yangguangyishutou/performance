以下是将Java代码翻译成C++的版本。假设相关的依赖项（如`LangUtils`）已经实现。

```cpp
#include <string>
#include <utility>
#include <stdexcept>

class NameValuePair {
public:
    // 默认构造函数
    NameValuePair() : name(nullptr), value(nullptr) {}

    // 带参数的构造函数
    NameValuePair(const std::string& name, const std::string& value) : name(name), value(value) {}

    // 设置名称
    void setName(const std::string& name) {
        this->name = name;
    }

    // 获取名称
    const std::string& getName() const {
        return name;
    }

    // 设置值
    void setValue(const std::string& value) {
        this->value = value;
    }

    // 获取值
    const std::string& getValue() const {
        return value;
    }

    // 获取字符串表示
    std::string toString() const {
        return "name=" + name + ", value=" + value;
    }

    // 重载等于运算符
    bool operator==(const NameValuePair& other) const {
        if (this == &other) return true;
        return LangUtils::equals(this->name, other.name) && LangUtils::equals(this->value, other.value);
    }

    // 重载不等于运算符
    bool operator!=(const NameValuePair& other) const {
        return !(*this == other);
    }

    // 获取哈希码
    int hashCode() const {
        int hash = LangUtils::HASH_SEED;
        hash = LangUtils::hashCode(hash, this->name);
        hash = LangUtils::hashCode(hash, this->value);
        return hash;
    }

private:
    std::string name;
    std::string value;
};

// 假设LangUtils类已经实现
class LangUtils {
public:
    static const int HASH_SEED = 17;

    static bool equals(const std::string& str1, const std::string& str2) {
        return str1 == str2;
    }

    static int hashCode(int seed, const std::string& str) {
        int result = seed;
        if (str.empty()) {
            return result;
        }
        for (char c : str) {
            result = 31 * result + c;
        }
        return result;
    }
};
```

### 说明：
1. **构造函数**：C++中的构造函数与Java类似，但不需要显式调用`this`来区分成员变量和参数。
2. **成员变量**：C++中使用`std::string`来表示字符串，而不是Java中的`String`。
3. **方法**：C++中的方法可以直接访问成员变量，不需要使用`this`关键字。
4. **字符串表示**：C++中使用`std::string`的`+`运算符来连接字符串。
5. **相等性检查**：C++中重载了`==`运算符来实现相等性检查。
6. **哈希码**：C++中使用`hashCode`方法来计算哈希码，类似于Java中的`hashCode`方法。

### 依赖项：
- `LangUtils`类假设已经实现，并提供了`equals`和`hashCode`方法。

这个C++代码与原始Java代码的功能基本一致，但使用了C++的语法和标准库。