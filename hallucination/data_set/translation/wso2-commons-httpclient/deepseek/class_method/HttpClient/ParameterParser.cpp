以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，例如`NameValuePair`类和`std::list`容器。

```cpp
#include <string>
#include <list>
#include <algorithm>
#include <cctype>
#include <stdexcept>

class NameValuePair {
public:
    NameValuePair(const std::string& name, const std::string& value)
        : name(name), value(value) {}

    std::string getName() const { return name; }
    std::string getValue() const { return value; }

private:
    std::string name;
    std::string value;
};

class ParameterParser {
public:
    ParameterParser() = default;

    std::list<NameValuePair> parse(const std::string& str, char separator) {
        if (str.empty()) {
            return {};
        }
        return parse(str.c_str(), separator);
    }

    std::list<NameValuePair> parse(const char* chars, char separator) {
        if (!chars) {
            return {};
        }
        return parse(chars, 0, std::strlen(chars), separator);
    }

    std::list<NameValuePair> parse(const char* chars, int offset, int length, char separator) {
        if (!chars) {
            return {};
        }

        std::list<NameValuePair> params;
        this->chars = chars;
        this->pos = offset;
        this->len = length;

        std::string paramName;
        std::string paramValue;

        while (hasChar()) {
            paramName = parseToken({'=', separator});
            paramValue = "";
            if (hasChar() && chars[pos] == '=') {
                pos++; // skip '='
                paramValue = parseQuotedToken({separator});
            }
            if (hasChar() && chars[pos] == separator) {
                pos++; // skip separator
            }
            if (!paramName.empty() || !paramValue.empty()) {
                params.emplace_back(paramName, paramValue);
            }
        }

        return params;
    }

private:
    const char* chars = nullptr;
    int pos = 0;
    int len = 0;
    int i1 = 0;
    int i2 = 0;

    bool hasChar() const {
        return pos < len;
    }

    std::string getToken(bool quoted) {
        // Trim leading white spaces
        while (i1 < i2 && std::isspace(chars[i1])) {
            i1++;
        }
        // Trim trailing white spaces
        while (i2 > i1 && std::isspace(chars[i2 - 1])) {
            i2--;
        }
        // Strip away quotes if necessary
        if (quoted) {
            if ((i2 - i1) >= 2 && chars[i1] == '"' && chars[i2 - 1] == '"') {
                i1++;
                i2--;
            }
        }
        if (i2 >= i1) {
            return std::string(chars + i1, i2 - i1);
        }
        return "";
    }

    bool isOneOf(char ch, const std::initializer_list<char>& charray) {
        return std::find(charray.begin(), charray.end(), ch) != charray.end();
    }

    std::string parseToken(const std::initializer_list<char>& terminators) {
        char ch;
        i1 = pos;
        i2 = pos;
        while (hasChar()) {
            ch = chars[pos];
            if (isOneOf(ch, terminators)) {
                break;
            }
            i2++;
            pos++;
        }
        return getToken(false);
    }

    std::string parseQuotedToken(const std::initializer_list<char>& terminators) {
        char ch;
        i1 = pos;
        i2 = pos;
        bool quoted = false;
        bool charEscaped = false;
        while (hasChar()) {
            ch = chars[pos];
            if (!quoted && isOneOf(ch, terminators)) {
                break;
            }
            if (!charEscaped && ch == '"') {
                quoted = !quoted;
            }
            charEscaped = (!charEscaped && ch == '\\');
            i2++;
            pos++;
        }
        return getToken(true);
    }
};
```

### 主要变化点：
1. **字符串处理**：Java中的`String`类在C++中被替换为`std::string`。
2. **数组处理**：Java中的`char[]`在C++中被替换为`const char*`。
3. **列表处理**：Java中的`List`在C++中被替换为`std::list`。
4. **字符串长度**：Java中的`String.length()`在C++中被替换为`std::strlen()`。
5. **字符串构造**：Java中的`new String(chars, i1, i2 - i1)`在C++中被替换为`std::string(chars + i1, i2 - i1)`。
6. **异常处理**：Java中的`null`检查在C++中被替换为`nullptr`检查。

### 注意事项：
- C++中的字符串处理与Java有所不同，特别是在处理字符数组和字符串长度时。
- C++中的`std::list`与Java中的`List`接口不完全相同，但功能相似。
- C++中的`std::initializer_list`用于传递字符数组，类似于Java中的`char[]`。

这个C++版本的代码应该能够实现与原始Java代码相同的功能。