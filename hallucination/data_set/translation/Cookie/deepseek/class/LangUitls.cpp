#include <cstdint>
#include <memory>
#include <functional>

class LangUtils {
public:
    static const int HASH_SEED = 17;
    static const int HASH_OFFSET = 37;

private:
    LangUtils() = default; // 私有构造函数，防止实例化

public:
    static int hashCode(int seed, int hashcode) {
        return seed * HASH_OFFSET + hashcode;
    }

    static int hashCode(int seed, const std::shared_ptr<void>& obj) {
        return hashCode(seed, obj ? std::hash<std::shared_ptr<void>>()(obj) : 0);
    }

    static int hashCode(int seed, bool b) {
        return hashCode(seed, b ? 1 : 0);
    }

    static bool equals(const std::shared_ptr<void>& obj1, const std::shared_ptr<void>& obj2) {
        if (obj1 == nullptr) {
            return obj2 == nullptr;
        }
        return obj1->equals(obj2);
    }
};

/*
说明：
私有构造函数：在C++中，我们使用= default来定义一个默认的私有构造函数，以防止类被实例化。

智能指针：在C++中，我们使用std::shared_ptr<void>来表示任意类型的对象指针。这样可以避免直接使用原始指针，并且可以方便地处理空指针的情况。

hashCode方法：在C++中，我们假设对象具有hashCode()方法，并且使用std::hash来计算对象的哈希值。

equals方法：在C++中，我们假设对象具有equals()方法，用于比较两个对象是否相等。

依赖项：
假设C++中的对象具有hashCode()和equals()方法。

假设std::hash模板可以用于计算对象的哈希值。

注意事项：
在实际使用中，可能需要根据具体的对象类型来调整hashCode和equals方法的实现。

如果对象类型是自定义的，可能需要为这些类型提供hashCode和equals方法的具体实现。
*/