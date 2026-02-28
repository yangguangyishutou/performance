
```python
Translation Strategy for Cookie.java:
1. Memory Management: Replace Java's garbage collection with RAII
2. Collections: Map ArrayList to std::vector or std::list
3. String Handling: Convert String to std::string with const references
4. Null Checking: Replace Objects.requireNonNull() with assertions
5. Equality: Implement operator== and operator!= instead of equals()
6. Hash Code: Implement std::hash specialization
```