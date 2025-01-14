以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，并且C++中的对象和方法与Java中的对象和方法具有相同的语义。

```cpp
#include <cstdint>
#include <utility>

/**
 * A set of utility methods to help produce consistent Object#equals(Object) and
 * Object#hashCode methods.
 *  
 * @author <a href="mailto:oleg at ural.ru">Oleg Kalnichevski</a>
 * 
 * @since 3.0
 */
class LangUtils {
public:
    static constexpr int HASH_SEED = 17;
    static constexpr int HASH_OFFSET = 37;

private:
    LangUtils() = default;

public:
    static int hashCode(int seed, int hashcode) {
        return seed * HASH_OFFSET + hashcode;
    }

    static int hashCode(int seed, const std::shared_ptr<void>& obj) {
        return hashCode(seed, obj ? std::hash<std::shared_ptr<void>>{}(obj) : 0);
    }

    static int hashCode(int seed, bool b) {
        return hashCode(seed, b ? 1 : 0);
    }

    static bool equals(const std::shared_ptr<void>& obj1, const std::shared_ptr<void>& obj2) {
        return obj1 == nullptr ? obj2 == nullptr : *obj1 == *obj2;
    }
};
```

### 说明：
1. **`std::shared_ptr<void>`**: 在C++中，我们使用`std::shared_ptr<void>`来表示Java中的`Object`类型。`std::shared_ptr<void>`可以指向任何类型的对象，并且可以安全地进行类型擦除。

2. **`std::hash`**: C++标准库提供了`std::hash`模板，用于计算对象的哈希值。我们使用它来计算`std::shared_ptr<void>`指向的对象的哈希值。

3. **`equals`方法**: 在C++中，我们假设`std::shared_ptr<void>`指向的对象重载了`operator==`，以便进行相等性比较。

4. **`hashCode`方法**: 我们假设`std::shared_ptr<void>`指向的对象的哈希值可以通过`std::hash`模板计算。

5. **`constexpr`**: 在C++中，我们使用`constexpr`来定义编译时常量。

6. **`private`构造函数**: 在C++中，我们将构造函数设为`private`，以防止类的实例化，类似于Java中的`private`构造函数。

### 依赖项：
- 假设C++标准库中的`std::hash`和`std::shared_ptr`已经实现，并且`std::shared_ptr<void>`指向的对象重载了`operator==`。

### 注意事项：
- 在实际使用中，可能需要根据具体的对象类型进行调整，特别是`std::shared_ptr<void>`的使用，可能需要更具体的类型来替代。
- 如果需要处理原始指针或其他类型的对象，可能需要进一步调整代码。