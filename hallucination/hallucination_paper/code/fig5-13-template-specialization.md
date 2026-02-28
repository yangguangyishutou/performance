
```cpp
template<typename T>
class Calculator {
public:
    T add(T a, T b) { return a + b; }
};

// Specialization for string concatenation optimization
template<>
class Calculator<std::string> {
public:
    std::string add(const std::string& a, const std::string& b) {
        std::string result;
        result.reserve(a.size() + b.size()); // Pre-allocate
        result += a;
        result += b;
        return result;
    }
};
```