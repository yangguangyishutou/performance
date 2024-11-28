#include <iostream>
#include <stdexcept>

class Log {
public:
    virtual ~Log() = default; // 虚析构函数，确保多态性

    virtual bool isDebugEnabled() const = 0;
    virtual bool isErrorEnabled() const = 0;
    virtual bool isFatalEnabled() const = 0;
    virtual bool isInfoEnabled() const = 0;
    virtual bool isTraceEnabled() const = 0;
    virtual bool isWarnEnabled() const = 0;

    virtual void trace(const std::string& message) = 0;
    virtual void trace(const std::string& message, const std::exception& e) = 0;

    virtual void debug(const std::string& message) = 0;
    virtual void debug(const std::string& message, const std::exception& e) = 0;

    virtual void info(const std::string& message) = 0;
    virtual void info(const std::string& message, const std::exception& e) = 0;

    virtual void warn(const std::string& message) = 0;
    virtual void warn(const std::string& message, const std::exception& e) = 0;

    virtual void error(const std::string& message) = 0;
    virtual void error(const std::string& message, const std::exception& e) = 0;

    virtual void fatal(const std::string& message) = 0;
    virtual void fatal(const std::string& message, const std::exception& e) = 0;
};