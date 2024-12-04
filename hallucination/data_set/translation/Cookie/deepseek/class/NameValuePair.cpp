#include <string>
#include <utility>
#include <stdexcept>


#include "LangUitls.cpp"

/**
 * <p>A simple class encapsulating a name/value pair.</p>
 * 
 * @author <a href="mailto:bcholmes@interlog.com">B.C. Holmes</a>
 * @author Sean C. Sullivan
 * @author <a href="mailto:mbowler@GargoyleSoftware.com">Mike Bowler</a>
 * 
 * @version $Revision: 480424 $ $Date: 2006-11-29 06:56:49 +0100 (Wed, 29 Nov 2006) $
 * 
 */
class NameValuePair {
public:
    // ----------------------------------------------------------- Constructors

    /**
     * Default constructor.
     * 
     */
    NameValuePair() : name(nullptr), value(nullptr) {}

    /**
     * Constructor.
     * @param name The name.
     * @param value The value.
     */
    NameValuePair(const std::string& name, const std::string& value)
        : name(name), value(value) {}

    // ----------------------------------------------------- Instance Variables

    /**
     * Name.
     */
    std::string name;

    /**
     * Value.
     */
    std::string value;

    // ------------------------------------------------------------- Properties

    /**
     * Set the name.
     *
     * @param name The new name
     * @see #getName()
     */
    void setName(const std::string& name) {
        this->name = name;
    }

    /**
     * Return the name.
     *
     * @return String name The name
     * @see #setName(String)
     */
    const std::string& getName() const {
        return name;
    }

    /**
     * Set the value.
     *
     * @param value The new value.
     */
    void setValue(const std::string& value) {
        this->value = value;
    }

    /**
     * Return the current value.
     *
     * @return String value The current value.
     */
    const std::string& getValue() const {
        return value;
    }

    // --------------------------------------------------------- Public Methods

    /**
     * Get a String representation of this pair.
     * @return A string representation.
     */
    std::string toString() const {
        return "name=" + name + ", value=" + value;
    }

    bool equals(const NameValuePair& other) const {
        return LangUtils::equals(this->name, other.name) &&
               LangUtils::equals(this->value, other.value);
    }

    bool operator==(const NameValuePair& other) const {
        return equals(other);
    }

    bool operator!=(const NameValuePair& other) const {
        return !equals(other);
    }

    int hashCode() const {
        int hash = LangUtils::HASH_SEED;
        hash = LangUtils::hashCode(hash, this->name);
        hash = LangUtils::hashCode(hash, this->value);
        return hash;
    }
};

/*
说明：
构造函数：C++中的构造函数与Java中的构造函数类似，但不需要显式地调用this来初始化成员变量。

成员变量：在C++中，成员变量可以直接在类中声明，并且可以通过构造函数进行初始化。

方法：C++中的方法与Java中的方法类似，但需要注意返回类型和参数类型的声明。

字符串处理：C++中使用std::string来处理字符串，这与Java中的String类似。

equals和hashCode方法：在C++中，equals方法被重载为operator==，而hashCode方法保持不变。

依赖项：假设LangUtils类已经实现，并且提供了equals和hashCode方法。
*/