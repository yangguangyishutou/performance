from typing import List
import re

def enum_translate_prompt(java_enum_code:str) -> str:
    prompt = f"""
<system>
    You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.
</system>

<context>
    The following is a Java enum file. It contains the constants of an enum class, and it is supposed to be translated to a C++ header file.
```java
{java_enum_code}
```
</context>

<instruction>
    According to the above code, translate the Java enum to a C++ header file. Mark this part with <translated></translated> tags.
</instruction>
    """
    return prompt