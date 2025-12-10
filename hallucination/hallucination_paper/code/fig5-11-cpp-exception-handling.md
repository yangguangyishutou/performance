
```cpp
void processData() /* throws std::ios_base::failure, std::runtime_error */ {
    try {
        // Processing logic
    } catch (const std::ios_base::failure& e) {
        logger->error("IO error: {}", e.what());
        throw; // Re-throw with same type
    }
}
```