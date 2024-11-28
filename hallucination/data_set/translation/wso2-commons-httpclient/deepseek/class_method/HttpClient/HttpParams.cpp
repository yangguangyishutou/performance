以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现。

```cpp
#include <string>
#include <unordered_map>
#include <memory>

class HttpParams {
public:
    virtual ~HttpParams() = default;

    /**
     * Returns the parent collection that this collection will defer to
     * for a default value if a particular parameter is not explicitly
     * set in the collection itself.
     *
     * @return the parent collection to defer to, if a particular parameter
     * is not explicitly set in the collection itself.
     *
     * @see #setDefaults(HttpParams)
     */
    virtual std::shared_ptr<HttpParams> getDefaults() const = 0;

    /**
     * Assigns the parent collection that this collection will defer to
     * for a default value if a particular parameter is not explicitly
     * set in the collection itself.
     *
     * @param params the parent collection to defer to, if a particular
     * parameter is not explicitly set in the collection itself.
     *
     * @see #getDefaults()
     */
    virtual void setDefaults(const std::shared_ptr<HttpParams>& params) = 0;

    /**
     * Returns a parameter value with the given name. If the parameter is
     * not explicitly defined in this collection, its value will be drawn
     * from a higher level collection at which this parameter is defined.
     * If the parameter is not explicitly set anywhere up the hierarchy,
     * <tt>nullptr</tt> value is returned.
     *
     * @param name the parent name.
     *
     * @return an object that represents the value of the parameter.
     *
     * @see #setParameter(String, Object)
     */
    virtual std::shared_ptr<void> getParameter(const std::string& name) const = 0;

    /**
     * Assigns the value to the parameter with the given name.
     *
     * @param name parameter name
     * @param value parameter value
     */
    virtual void setParameter(const std::string& name, const std::shared_ptr<void>& value) = 0;

    /**
     * Returns a {@link long} parameter value with the given name.
     * If the parameter is not explicitly defined in this collection, its
     * value will be drawn from a higher level collection at which this parameter
     * is defined. If the parameter is not explicitly set anywhere up the hierarchy,
     * the default value is returned.
     *
     * @param name the parent name.
     * @param defaultValue the default value.
     *
     * @return a {@link long} that represents the value of the parameter.
     *
     * @see #setLongParameter(String, long)
     */
    virtual long getLongParameter(const std::string& name, long defaultValue) const = 0;

    /**
     * Assigns a {@link long} to the parameter with the given name.
     *
     * @param name parameter name
     * @param value parameter value
     */
    virtual void setLongParameter(const std::string& name, long value) = 0;

    /**
     * Returns an {@link int} parameter value with the given name.
     * If the parameter is not explicitly defined in this collection, its
     * value will be drawn from a higher level collection at which this parameter
     * is defined. If the parameter is not explicitly set anywhere up the hierarchy,
     * the default value is returned.
     *
     * @param name the parent name.
     * @param defaultValue the default value.
     *
     * @return a {@link int} that represents the value of the parameter.
     *
     * @see #setIntParameter(String, int)
     */
    virtual int getIntParameter(const std::string& name, int defaultValue) const = 0;

    /**
     * Assigns an {@link int} to the parameter with the given name.
     *
     * @param name parameter name
     * @param value parameter value
     */
    virtual void setIntParameter(const std::string& name, int value) = 0;

    /**
     * Returns a {@link double} parameter value with the given name.
     * If the parameter is not explicitly defined in this collection, its
     * value will be drawn from a higher level collection at which this parameter
     * is defined. If the parameter is not explicitly set anywhere up the hierarchy,
     * the default value is returned.
     *
     * @param name the parent name.
     * @param defaultValue the default value.
     *
     * @return a {@link double} that represents the value of the parameter.
     *
     * @see #setDoubleParameter(String, double)
     */
    virtual double getDoubleParameter(const std::string& name, double defaultValue) const = 0;

    /**
     * Assigns a {@link double} to the parameter with the given name.
     *
     * @param name parameter name
     * @param value parameter value
     */
    virtual void setDoubleParameter(const std::string& name, double value) = 0;

    /**
     * Returns a {@link bool} parameter value with the given name.
     * If the parameter is not explicitly defined in this collection, its
     * value will be drawn from a higher level collection at which this parameter
     * is defined. If the parameter is not explicitly set anywhere up the hierarchy,
     * the default value is returned.
     *
     * @param name the parent name.
     * @param defaultValue the default value.
     *
     * @return a {@link bool} that represents the value of the parameter.
     *
     * @see #setBooleanParameter(String, bool)
     */
    virtual bool getBooleanParameter(const std::string& name, bool defaultValue) const = 0;

    /**
     * Assigns a {@link bool} to the parameter with the given name.
     *
     * @param name parameter name
     * @param value parameter value
     */
    virtual void setBooleanParameter(const std::string& name, bool value) = 0;

    /**
     * Returns <tt>true</tt> if the parameter is set at any level, <tt>false</tt> otherwise.
     *
     * @param name parameter name
     *
     * @return <tt>true</tt> if the parameter is set at any level, <tt>false</tt>
     * otherwise.
     */
    virtual bool isParameterSet(const std::string& name) const = 0;

    /**
     * Returns <tt>true</tt> if the parameter is set locally, <tt>false</tt> otherwise.
     *
     * @param name parameter name
     *
     * @return <tt>true</tt> if the parameter is set locally, <tt>false</tt>
     * otherwise.
     */
    virtual bool isParameterSetLocally(const std::string& name) const = 0;

    /**
     * Returns <tt>true</tt> if the parameter is set and is <tt>true</tt>, <tt>false</tt>
     * otherwise.
     *
     * @param name parameter name
     *
     * @return <tt>true</tt> if the parameter is set and is <tt>true</tt>, <tt>false</tt>
     * otherwise.
     */
    virtual bool isParameterTrue(const std::string& name) const = 0;

    /**
     * Returns <tt>true</tt> if the parameter is either not set or is <tt>false</tt>,
     * <tt>false</tt> otherwise.
     *
     * @param name parameter name
     *
     * @return <tt>true</tt> if the parameter is either not set or is <tt>false</tt>,
     * <tt>false</tt> otherwise.
     */
    virtual bool isParameterFalse(const std::string& name) const = 0;
};
```

### 说明：
1. **接口定义**：在C++中，接口通常通过纯虚函数（`= 0`）来实现。`HttpParams`类中的所有方法都是纯虚函数，因此它是一个抽象基类。
2. **智能指针**：为了管理对象的生命周期，使用了`std::shared_ptr`。
3. **类型转换**：在Java中，`Object`类型可以容纳任何对象，但在C++中，我们使用`std::shared_ptr<void>`来表示泛型对象。
4. **默认值**：对于基本类型的默认值，直接在方法签名中传递。

这个C++接口类可以被继承并实现具体的参数管理逻辑。