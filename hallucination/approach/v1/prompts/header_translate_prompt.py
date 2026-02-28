from typing import List
import re

def header_translate_prompt(java_class_skeleton:str, scheme:str, additional_file_names:List[str], implemented_additional_file_names:list[str]):
    java_code = java_class_skeleton

    prompt = f"""
<system>
    You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.
</system>

<context>
    The following is a part of java file. it contians the member varables and member functions(the function implements are omitted). 
```java
{java_code}
```
    Now, it is supposed to be translated to a C++ header file.
</context>

<scheme>
    The following is the translation scheme:
{scheme}
</scheme>

<instruction>
    1. According to the above translation plan, provide the translated code. Mark this part with <translated></translated> tags.
    2. Explain each translated method and field declaration corresponding to the original Java function declaration in the form of comments.
{
    ("    3. Declare the necessary fields and methods of the following custom classes:"
    + "\n      ".join(additional_file_names) +
    "\n each class should be encased by ```cpp``` block, and add the file name in the first line of the block(like '// MyClass.h', do not add other text in the same line). Mark this part with <external-class></external-class> tags;")
    if len(additional_file_names) > 0 else ""
}
</instruction>

<note>
    1. Only header file is required, don’t implement the methods;
    2. If you have used a custom class, include its header file(the header file name is composed of the class name + ".h")
    3. For **each** translated member variable or member function declaration, mark the original Java member variable or method signature with a comment on the **same line**. 
    4. When you annotate a Java method signature after a C++ method declaration, please ensure that **only the variable types, not the variable names**, are retained in the parameters of the Java method signature. For example, the method add(Int a, Int b) must be written as // `add(Int,Int)`
    5. If you declare a pure virtual class corresponding to a Java interface, please ensure that they have at least one virtual method.
    {"6. the following header files can be directly included and don't need to be declared:"
     + ",".join(implemented_additional_file_names) if len(implemented_additional_file_names) > 0 else ""}
</note>

<example>
    here is an output example:
    <translated>
        ```cpp
        #ifndef EXAMPLE_H
        #define EXAMPLE_H
        #include <vector>
        #include <string>
        #include "MyClass.h"
        #include "MyInterface.h"

        class Example: public MyClass, public MyInterface {{
        protected:
            int a; // `int a`
            std::string b; // `String b`

            void method1(std::string& u, std::string v); // `method1(String,String)`
            std::vector<std::string>* method2(int i); // `method2(int)`
        }};
        #endif // EXAMPLE_H
        ```
    </translated>

    {"""<external-class>
        ```cpp
        // MyClass.h
        #ifndef MYCLASS_H
        #define MYCLASS_H

        class MyClass {{
            // neccessary fields and methods declarations.
        }};
     
        #endif // MYCLASS_H
        ```
        ```cpp
        // MyInterface.h
        #ifndef MYINTERFACE_H
        #define MYINTERFACE_H
        class MyInterface {{
            // neccessary methods declarations.
        }};
        #endif // MYINTERFACE_H
        ```
    </external-class>""" if len(additional_file_names) > 0 else ""}
</example>
    """
    return prompt