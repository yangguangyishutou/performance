
```cpp
template<typename T>
class Container {
private:
    T item;
    std::unique_ptr<T> item_ptr;

public:
    Container() = default;

    explicit Container(const T& item) : item(item) {}

    explicit Container(T&& item) : item(std::move(item)) {}

    const T& getItem() const {
        return item;
    }

    void setItem(const T& new_item) {
        item = new_item;
    }

    void setItem(T&& new_item) {
        item = std::move(new_item);
    }

    bool isEmpty() const {
        return item_ptr == nullptr;
    }
};
```