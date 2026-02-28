
```java
import java.util.List;
import java.util.ArrayList;
import java.util.Objects;

public class Cookie {
    private String name;
    private String value;
    private List<String> attributes;

    public Cookie(String name, String value) {
        this.name = Objects.requireNonNull(name);
        this.value = Objects.requireNonNull(value);
        this.attributes = new ArrayList<>();
    }

    public String getName() {
        return name;
    }

    public void addAttribute(String attr) {
        attributes.add(Objects.requireNonNull(attr));
    }

    public List<String> getAttributes() {
        return new ArrayList<>(attributes);
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;
        Cookie cookie = (Cookie) obj;
        return Objects.equals(name, cookie.name) &&
               Objects.equals(value, cookie.value);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, value);
    }
}
```