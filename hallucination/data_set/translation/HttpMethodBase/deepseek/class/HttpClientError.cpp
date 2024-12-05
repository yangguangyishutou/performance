以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，并且C++标准库已经包含在内。

```cpp
#include <stdexcept>
#include <string>

/**
 * Signals that an error has occurred.
 * 
 * @author Ortwin Glueck
 * @version $Revision: 480424 $ $Date: 2006-11-29 06:56:49 +0100 (Wed, 29 Nov 2006) $
 * @since 3.0
 */
class HttpClientError : public std::runtime_error {
public:
    /**
     * Creates a new HttpClientError with a <tt>null</tt> detail message.
     */
    HttpClientError() : std::runtime_error("") {}

    /**
     * Creates a new HttpClientError with the specified detail message.
     * @param message The error message
     */
    HttpClientError(const std::string& message) : std::runtime_error(message) {}
};
```

### 解释：
1. **继承**：在C++中，`HttpClientError` 类继承自 `std::runtime_error`，类似于Java中的 `Error` 类。`std::runtime_error` 是C++标准库中用于表示运行时错误的类。

2. **构造函数**：
   - 默认构造函数 `HttpClientError()` 创建一个没有详细信息的错误对象。
   - 带参数的构造函数 `HttpClientError(const std::string& message)` 创建一个带有指定错误信息的错误对象。

3. **字符串类型**：在C++中，字符串类型是 `std::string`，而不是Java中的 `String`。

4. **异常处理**：在C++中，异常处理通常使用 `try-catch` 块来捕获和处理异常，这与Java中的异常处理机制类似。

### 使用示例：
```cpp
try {
    // Some code that might throw an HttpClientError
    throw HttpClientError("An error occurred in the HTTP client.");
} catch (const HttpClientError& e) {
    std::cerr << "HttpClientError caught: " << e.what() << std::endl;
}
```

在这个示例中，`e.what()` 方法返回错误信息，类似于Java中的 `getMessage()` 方法。