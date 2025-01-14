以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，例如`URLCodec`、`NameValuePair`、`Log`、`LogFactory`等。

```cpp
#include <string>
#include <vector>
#include <stdexcept>
#include <sstream>
#include <iostream>
#include <cstring>
#include <cstdlib>
#include <cerrno>
#include <codecvt>
#include <locale>

// 假设这些依赖项已经实现
class URLCodec;
class NameValuePair;
class Log;
class LogFactory;

class EncodingUtil {
public:
    static const std::string DEFAULT_CHARSET;
    static const std::string STRICT;
    static const std::string ALLOW_ALL;
    static const std::string DEFAULT_AND_LOCALHOST;
    static const std::string HOST_NAME_VERIFIER;

private:
    static Log* LOG;

public:
    static std::string formUrlEncode(const std::vector<NameValuePair>& pairs, const std::string& charset) {
        try {
            return doFormUrlEncode(pairs, charset);
        } catch (const std::invalid_argument& e) {
            LOG->error("Encoding not supported: " + charset);
            try {
                return doFormUrlEncode(pairs, DEFAULT_CHARSET);
            } catch (const std::invalid_argument& fatal) {
                throw std::runtime_error("Encoding not supported: " + DEFAULT_CHARSET);
            }
        }
    }

private:
    static std::string doFormUrlEncode(const std::vector<NameValuePair>& pairs, const std::string& charset) {
        std::ostringstream buf;
        for (size_t i = 0; i < pairs.size(); ++i) {
            URLCodec codec;
            const NameValuePair& pair = pairs[i];
            if (pair.getName().length() > 0) {
                if (i > 0) {
                    buf << "&";
                }
                buf << codec.encode(pair.getName(), charset) << "=";
                if (pair.getValue().length() > 0) {
                    buf << codec.encode(pair.getValue(), charset);
                }
            }
        }
        return buf.str();
    }

public:
    static std::string getString(const std::vector<char>& data, int offset, int length, const std::string& charset) {
        if (data.empty()) {
            throw std::invalid_argument("Parameter may not be null");
        }

        if (charset.empty()) {
            throw std::invalid_argument("charset may not be null or empty");
        }

        try {
            std::wstring_convert<std::codecvt_utf8<wchar_t>> converter;
            std::wstring wstr = converter.from_bytes(&data[offset], &data[offset + length]);
            return converter.to_bytes(wstr);
        } catch (const std::range_error& e) {
            if (LOG->isWarnEnabled()) {
                LOG->warn("Unsupported encoding: " + charset + ". System encoding used");
            }
            return std::string(&data[offset], length);
        }
    }

    static std::string getString(const std::vector<char>& data, const std::string& charset) {
        return getString(data, 0, data.size(), charset);
    }

    static std::vector<char> getBytes(const std::string& data, const std::string& charset) {
        if (data.empty()) {
            throw std::invalid_argument("data may not be null");
        }

        if (charset.empty()) {
            throw std::invalid_argument("charset may not be null or empty");
        }

        try {
            std::wstring_convert<std::codecvt_utf8<wchar_t>> converter;
            std::wstring wstr = converter.from_bytes(data);
            return std::vector<char>(converter.to_bytes(wstr).begin(), converter.to_bytes(wstr).end());
        } catch (const std::range_error& e) {
            if (LOG->isWarnEnabled()) {
                LOG->warn("Unsupported encoding: " + charset + ". System encoding used.");
            }
            return std::vector<char>(data.begin(), data.end());
        }
    }

    static std::vector<char> getAsciiBytes(const std::string& data) {
        if (data.empty()) {
            throw std::invalid_argument("Parameter may not be null");
        }

        try {
            return std::vector<char>(data.begin(), data.end());
        } catch (const std::range_error& e) {
            throw std::runtime_error("HttpClient requires ASCII support");
        }
    }

    static std::string getAsciiString(const std::vector<char>& data, int offset, int length) {
        if (data.empty()) {
            throw std::invalid_argument("Parameter may not be null");
        }

        try {
            return std::string(&data[offset], length);
        } catch (const std::range_error& e) {
            throw std::runtime_error("HttpClient requires ASCII support");
        }
    }

    static std::string getAsciiString(const std::vector<char>& data) {
        return getAsciiString(data, 0, data.size());
    }

private:
    EncodingUtil() {}
};

const std::string EncodingUtil::DEFAULT_CHARSET = "ISO-8859-1";
const std::string EncodingUtil::STRICT = "Strict";
const std::string EncodingUtil::ALLOW_ALL = "AllowAll";
const std::string EncodingUtil::DEFAULT_AND_LOCALHOST = "DefaultAndLocalhost";
const std::string EncodingUtil::HOST_NAME_VERIFIER = "httpclient.hostnameVerifier";

Log* EncodingUtil::LOG = LogFactory::getLog("EncodingUtil");
```

### 说明：
1. **依赖项**：假设`URLCodec`、`NameValuePair`、`Log`、`LogFactory`等类已经实现，并且具有与Java版本相同的功能。
2. **异常处理**：在C++中，异常处理使用`std::invalid_argument`和`std::runtime_error`来替代Java中的`UnsupportedEncodingException`和`HttpClientError`。
3. **字符编码转换**：使用`std::wstring_convert`和`std::codecvt_utf8`来进行字符编码转换，这与Java中的字符编码转换类似。
4. **日志记录**：假设`Log`类具有与Java中的`Log`类相同的功能，包括`error`、`warn`和`isWarnEnabled`等方法。

请根据实际需求和依赖项的实现情况进行调整。