"""
enum 的翻译提示
后期可能会增加额外类字段
"""

from typing import List
import re



def header_translate_prompt_enum(java_enum_code:str) -> str:
    json_example = """```json
{
    "class_name": "ExampleClass",
    "type": "class/enum class/...",
    "translated_code": "#include <string>
    enum class ExampleEnum { ... }"
}
```
    """
    return f"""
You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.

The following is a Java enum file. It contains the constants of an enum class, and it is supposed to be translated to a C++ header file.
```java
{java_enum_code}
```
According to the above code, translate the Java enum to a C++ header file. The answer should be in JSON format:
{json_example}
    """

enum_translate_output_schema = {
    "type": "object",
    "properties": {
        "enum_name": {
            "type": "string"
        },
        "translated_code": {
            "type": "string"
        }
    }
    
}

    
#     prompt = f"""
# <system>
#     You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.
# </system>

# <context>
#     The following is a Java enum file. It contains the constants of an enum class, and it is supposed to be translated to a C++ header file.
# ```java
# {java_enum_code}
# ```
# </context>

# <instruction>
#     According to the above code, translate the Java enum to a C++ header file. Mark this part with <translated></translated> tags.
# </instruction>
#     """
#     return prompt