
```cpp
class ResourceManager {
private:
    std::unique_ptr<Resource> resource;

public:
    ResourceManager() : resource(std::make_unique<Resource>()) {}

    // Destructor automatically closes resource
    ~ResourceManager() {
        if (resource) {
            resource->close();
        }
    }

    // Rule of five
    ResourceManager(const ResourceManager&) = delete;
    ResourceManager& operator=(const ResourceManager&) = delete;
    ResourceManager(ResourceManager&&) = default;
    ResourceManager& operator=(ResourceManager&&) = default;
};
```