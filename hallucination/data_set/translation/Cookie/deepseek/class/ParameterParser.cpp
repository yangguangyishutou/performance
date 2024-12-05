#include <vector>
#include <string>
#include <algorithm>
#include <cctype>

class NameValuePair {
public:
    std::string name;
    std::string value;

    NameValuePair(const std::string& name, const std::string& value)
        : name(name), value(value) {}
};

/**
 * A simple parser intended to parse sequences of name/value pairs.
 * Parameter values are expected to be enclosed in quotes if they 
 * contain unsafe characters, such as '=' characters or separators.
 * Parameter values are optional and can be omitted. 
 * 
 * <p>
 *  <code>param1 = value; param2 = "anything goes; really"; param3</code>
 * </p>
 * 
 * @author <a href="mailto:oleg@ural.ru">Oleg Kalnichevski</a>
 * 
 * @since 3.0
 */
class ParameterParser {
private:
    /** String to be parsed */
    const char* chars = nullptr;
    
    /** Current position in the string */    
    int pos = 0;

    /** Maximum position in the string */    
    int len = 0;

    /** Start of a token */
    int i1 = 0;

    /** End of a token */
    int i2 = 0;
    
    /** Default ParameterParser constructor */
    ParameterParser() = default;

    /** Are there any characters left to parse? */
    bool hasChar() const {
        return this->pos < this->len;
    }

    /** A helper method to process the parsed token. */
    std::string getToken(bool quoted) const {
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
            if ((i2 - i1 >= 2) && (chars[i1] == '"') && (chars[i2 - 1] == '"')) {
                i1++;
                i2--;
            }
        }
        if (i2 >= i1) {
            return std::string(chars + i1, i2 - i1);
        }
        return std::string();
    }

    /** Is given character present in the array of characters? */
    bool isOneOf(char ch, const std::vector<char>& charray) const {
        return std::find(charray.begin(), charray.end(), ch) != charray.end();
    }
    
    /** Parse out a token until any of the given terminators
     * is encountered. */
    std::string parseToken(const std::vector<char>& terminators) {
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
    
    /** Parse out a token until any of the given terminators
     * is encountered. Special characters in quoted tokens
     * are escaped. */
    std::string parseQuotedToken(const std::vector<char>& terminators) {
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

public:
    /** 
     * Extracts a list of {@link NameValuePair}s from the given string.
     *
     * @param str the string that contains a sequence of name/value pairs
     * @return a list of {@link NameValuePair}s
     * 
     */
    std::vector<NameValuePair> parse(const std::string& str, char separator) {
        if (str.empty()) {
            return {};
        }
        return parse(str.c_str(), 0, str.length(), separator);
    }

    /** 
     * Extracts a list of {@link NameValuePair}s from the given array of 
     * characters.
     *
     * @param chars the array of characters that contains a sequence of 
     * name/value pairs
     * 
     * @return a list of {@link NameValuePair}s
     */
    std::vector<NameValuePair> parse(const char* chars, char separator) {
        if (chars == nullptr) {
            return {};
        }
        return parse(chars, 0, std::strlen(chars), separator);
    }

    /** 
     * Extracts a list of {@link NameValuePair}s from the given array of 
     * characters.
     *
     * @param chars the array of characters that contains a sequence of 
     * name/value pairs
     * @param offset - the initial offset.
     * @param length - the length.
     * 
     * @return a list of {@link NameValuePair}s
     */
    std::vector<NameValuePair> parse(const char* chars, int offset, int length, char separator) {
        if (chars == nullptr) {
            return {};
        }
        std::vector<NameValuePair> params;
        this->chars = chars;
        this->pos = offset;
        this->len = length;
        
        std::string paramName;
        std::string paramValue;
        while (hasChar()) {
            paramName = parseToken({'=', separator});
            paramValue = "";
            if (hasChar() && (chars[pos] == '=')) {
                pos++; // skip '='
                paramValue = parseQuotedToken({separator});
            }
            if (hasChar() && (chars[pos] == separator)) {
                pos++; // skip separator
            }
            if (!paramName.empty() || !paramValue.empty()) {
                params.emplace_back(paramName, paramValue);
            }
        }        
        return params;
    }
};

/*
主要变化点：
字符串处理：Java中的String类在C++中被替换为std::string。

数组处理：Java中的char[]在C++中被替换为const char*或std::vector<char>。

列表处理：Java中的List在C++中被替换为std::vector。

字符串长度：Java中的String.length()在C++中被替换为std::strlen()或std::string::length()。

字符串构造：Java中的new String(chars, i1, i2 - i1)在C++中被替换为std::string(chars + i1, i2 - i1)。

字符查找：Java中的isOneOf方法在C++中使用std::find实现。

依赖项：
NameValuePair类需要实现，这里假设它是一个简单的类，包含name和value两个成员变量。
*/