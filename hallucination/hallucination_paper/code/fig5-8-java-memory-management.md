
```java
public class ResourceManager {
    private Resource resource;

    public ResourceManager() {
        this.resource = new Resource();
    }

    public void close() {
        if (resource != null) {
            resource.close();
            resource = null;
        }
    }
}
```