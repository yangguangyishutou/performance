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

    // 比较两个NameValuePair对象是否相等
    bool equals(const NameValuePair& other) const {
        if (this == &other) return true;
        return LangUtils::equals(this->name, other.name) && LangUtils::equals(this->value, other.value);
    }

    // 计算哈希码
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

    static int hashCode(int hash, const std::string& str) {
        return 31 * hash + (str.empty() ? 0 : std::hash<std::string>{}(str));
    }
};
```

### 说明：
1. **构造函数**：C++中的构造函数与Java类似，但不需要显式地调用`this`来区分成员变量和参数。
2. **成员变量**：在C++中，成员变量可以直接在类中声明并初始化。
3. **方法**：C++中的方法与Java中的方法类似，但需要注意返回类型和参数类型的声明。
4. **字符串处理**：使用`std::string`来处理字符串，这与Java中的`String`类类似。
5. **哈希和相等性**：假设`LangUtils`类已经实现，并提供了`equals`和`hashCode`方法。

这个C++代码实现了与Java代码相同的功能，并且假设`LangUtils`类已经实现了必要的静态方法。