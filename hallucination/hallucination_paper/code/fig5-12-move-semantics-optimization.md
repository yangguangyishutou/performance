
```cpp
class DataProcessor {
private:
    std::vector<std::string> data;

public:
    // Before: Copy semantics
    void setData(const std::vector<std::string>& input) {
        data = input; // Expensive copy
    }

    // After: Move semantics (automatically suggested by agent)
    void setData(std::vector<std::string>&& input) {
        data = std::move(input); // Efficient move
    }
};
```