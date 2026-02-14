# 错误类型

## 1. 引用不存在的方法或成员变量

```cpp
//例1:
if (visited.insert(current).second) {
    try {
        std::rethrow_exception(current);
    } catch (const std::exception& e) {
        if (e.getCause()) {
            toVisit.push_back(std::make_exception_ptr(*e.getCause()));
        }
        for (const auto& suppressed : e.getSuppressed()) {
            toVisit.push_back(std::make_exception_ptr(suppressed));
        }
    }
}
// 说明:
// exception类不包含方法getCause和getSuppressed
```

## 2. 参数表不匹配

```cpp
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
}
```

```cpp
//例1:
int hashCode() const {  //#2LangUtils::hashCode参数表不匹配
        int hash = LangUtils::HASH_SEED;
        hash = LangUtils::hashCode(hash, getName());
        hash = LangUtils::hashCode(hash, cookieDomain);
        hash = LangUtils::hashCode(hash, cookiePath);
        return hash;
    }
//说明:
// LangUtils::hashCode没有(int, string)的重载方法
```

## 3. 缺少头文件

```cpp
// 例1:
virtual std::set<std::string> getTags() const = 0;  //#3缺少库文件set
// 说明:
// set类在<set>中定义,但是文件中并未包含<set>
```

**注意:**
此类错误应与类型1、9、10区分:如果添加缺失的头文件后问题解决,则算作类型3,如果并没有这样的头文件,则说明使用的函数或类是凭空捏造的,算作1、9、10.(*注注意: 这两种情况仍不包含项目中存在的类或方法*)

## 4. 方法未实现(全部缺失)

```cpp
// 例1
void notifyListenersExpanding();  //#4无函数实现
// 说明:
// 仅给出了声明,没有给出具体实现(体外实现也没有)
```

```cpp
// 例2:

void notifyListenersExpanding();  

//...
//...
//...

void notifyListenersExpanding(){
    //具体实现
}

// 说明:
// 给了体外实现,但是没有具体内容
```

## 5. 代码逻辑/错误处理被简化（弃用）

此类型已并入类型11,请勿标注

## 6. 变量初始化/使用错误

```cpp
// 例
class FieldAttributes {
private:
    const Field& field;
}
// 说明:
// 引用必须在定义时初始化
```

## 7. 逻辑/语义与原代码不符  

此类型暂时弃用,请勿标注

## 8. 错误使用指针

```cpp
// 例：
class JsonPrimitive : public JsonElement {
private:
    std::shared_ptr<void> value;

    int hashCode() const {  //#7value是std::shared_ptr<void>类型，不能直接调用hashCode()方法
        if (!value) {
            return 31;
        }
        if (isIntegral(*this)) {
            long longValue = getAsNumber()->longValue();
            return static_cast<int>(longValue ^ (longValue >> 32));
        }
        if (isNumber()) {
            long longValue = *reinterpret_cast<long*>(&getAsNumber()->doubleValue());
            return static_cast<int>(longValue ^ (longValue >> 32));
        }
        return value->hashCode();
    }
}
// 说明:
// value的指针类型是void，不能直接访问成员
```

## 9. 引用不存在的类

```cpp
//例1：
const Date* getExpiryDate() const {   //#1不存在的类“Date“
    return cookieExpiryDate.get();
}
// 说明：
// C++中没有原生的Date类


//例2：
class Cookie : public NameValuePair, public Comparator {
// 说明:
// C++中没有原生的Comparator类
```

**注意：**
报错并不代表真的有错，如果该类存在于翻译列表中，则不算错

## 10. 方法部分未实现(部分缺失)  *注：此类型与5合并，即代码逻辑被简化也算作缺失

```cpp
// 例:
static bool initializeSqlTypesSupport() {  //#7没有真正实现类型的检查，逻辑不够完善
    try {
        // ģ��Java�е�Class.forName("java.sql.Date")
        // ��C++�У����ǿ���ͨ�����԰������ͷ�ļ���ʹ������������ģ��
        // �������Ǽ���֧��SQL����
        return true;
    } catch (const std::exception&) {
        return false;
    }
}
// 说明
// 类型检查未实现
```

## 11. 内存管理不当

一般指内存申请或释放时出错或内存泄露（申请了不释放）
