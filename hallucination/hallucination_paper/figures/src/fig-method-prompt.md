```xml
<system>
    You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.
</system>

<context>
    The following is a Java method from class {class_name}
    ```java
    {java_method_code}
    ```
    Now, it is supposed to be translated to the following C++ method:
    {translated_cpp_declaration}
</context>

<scheme>
Translation Scheme:
{scheme}
</scheme>

<instruction>
    1. Provide the translated C++ method implementation based on the above scheme, mark this part with <implementation></implementation> tags.
    2. Include the necessary header files (include the "{class_name}.h")
    3. Declare the classes and methods in <additional-class> and <additional-method> tags (if any) in a /"temp_header.h/" file. Mark this part with <dependency></dependency> tags.
</instruction>

<note>
    - The header file has already been written. You just need to write the out-of-body implementation of this function, and there's no need to repeat the class and field declarations.
    - remember to include /"{class_name}.h/"
    - The followings are the fields of the class {class_name} for reference:{class_fields}
    - The following classes and methods have already been implemented, you can just include them instead of re-declaring.
    {external_methods_implementations_str}
</note>

<example>
    For example, for the method `std::string Example::method1(std::string a, const std::vector<std::string>& l, Processor p)`, your answer should look like this:
    <implementation>
    ```cpp
    #include <vector>
    #include <string>
    #include "Example.h"
    #include "temp_header.h"

    std::string Example::method1(std::string a, const std::vector<std::string>& l, Processor p) {{
        vector<string> new_vector(l);
        new_vector.push_back(a);
        string joined = join(new_vector, ",");
        return p.process(joined);
    }}
    ```
    </implementation>

    <dependency>
    ```cpp
    // this is a temporary header file, containing only the necessary declarations
    #include <vector>
    #include <string>

    class Processor {{
    public:
        std::string process(const std::string& input) const;
    }};

    std::string join(const std::vector<std::string>& vec, const std::string& delimiter);
    ```
    </dependency>
</example>
```