
```java
public void processData() throws IOException, SQLException {
    try {
        // Processing logic
    } catch (IOException e) {
        logger.error("IO error", e);
        throw e;
    }
}
```