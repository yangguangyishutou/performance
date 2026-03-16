from typing import List

def header_translate_prompt_class(java_skeleton:str, scheme:str, all_method_signatures:str, header_file_list:str):
    """
    java_skeleton: java类的骨架，包含字段和方法的声明
    scheme: 翻译方案
    all_method_signatures: 该类所有需要声明的方法签名，这里是java方法签名
    header_file_list: 所有可用的头文件名，包括项目中的文件和目前已经添加的额外文件
    """

    json_example = """```json
{
    "class_name": "ExampleClass",
    "type": "concrete class/abstract class/virtual base class/...",
    "translated_code": "#include <string> 
    #include<vector>
    class ExampleClass { ... }",
    "field_mapping":[
        {
            "original": "java_field_name", // if it is a new field added during translation, leave it an empty string.
            "translated": "cpp_field_name" // if the original field is removed during translation, leave it an empty string.
        },
        {
            ...
        }
    ],
    "method_mapping":[ // the method signature only contains the method name and the parameter types (no parameter names and return type), for example: add(int,int)
        {
            "original": "java_method_signature", // if it is a new method added during translation, leave it an empty string.
            "translated": "cpp_method_declaration", // if the original method is removed during translation, leave it an empty string.
            "main_function": "calculate the sum of two numbers"
        },
        {
            ...
        }
    ],
    "external_header_files":[ // If there is none, leave it blank.
        {
            "file_name": "external_class_name.h",
            "content": "..."
        },
        {
            ...
        }
    ]
}
```
(The comments in the above json content are for explanation only. When actually outputting, please strictly abide by the json syntax and do not add comments.)
    """

    return f"""
You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.

The following is a part of java file from the source repository. it contians the member varables and member functions(the function implements are omitted). Now it is supposed to be translated to a C++ header file.
{java_skeleton}

The following is the translation scheme:
{scheme}

According to the above translation plan, provide the translated result, your answer should include:
1. The translated code;
2. Mapping between translated fields/methods and original java fields/methods.
3. The necessary external class declarations in translation plan(if any), they will be added to the translated repository as additional header files.

The available header files in the current project are as follows. If you need to use a header file that is not included in them, please add it to the list of external header files.
{header_file_list}

The answer should be in the format of json:
{json_example}

Notes:
1. Only header file is required, don’t implement the methods;
2. the "method_mapping" should at least include the following method signatures:{all_method_signatures or "(empty)"}
    """

class_translate_output_schema = {
    "type": "object",
    "properties": {
        "translated_code": {
            "type": "string"
        },
        "field_mapping": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {
                        "type": "string"
                    },
                    "translated": {
                        "type": "string"
                    }
                }
            }
        },
        "method_mapping": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {
                        "type": "string"
                    },
                    "translated": {
                        "type": "string"
                    },
                    "main_function": {
                        "type": "string"
                    }
                }
            }
        },
        "external_header_files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string"
                    },
                    "content": {
                        "type": "string"
                    }
                }
            }
        }
    }
}
#     You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.
# </system>

# <context>
#     The following is a part of java file. it contians the member varables and member functions(the function implements are omitted). 
# ```java
# {java_code}
# ```
#     Now, it is supposed to be translated to a C++ header file.
# </context>

# <scheme>
#     The following is the translation scheme:
# {scheme}
# </scheme>

# <instruction>
#     1. According to the above translation plan, provide the translated code. Mark this part with <translated></translated> tags.
#     2. Explain each translated method and field declaration corresponding to the original Java function declaration in the form of comments.
# {
#     ("    3. Declare the necessary fields and methods of the following custom classes:"
#     + "\n      ".join(additional_file_names) +
#     "\n each class should be encased by ```cpp``` block, and add the file name in the first line of the block(like '// MyClass.h', do not add other text in the same line). Mark this part with <external-class></external-class> tags;")
#     if len(additional_file_names) > 0 else ""
# }
# </instruction>

# <note>
#     1. Only header file is required, don’t implement the methods;
#     2. If you have used a custom class, include its header file(the header file name is composed of the class name + ".h")
#     3. For **each** translated member variable or member function declaration, mark the original Java member variable or method signature with a comment on the **same line**. 
#     4. When you annotate a Java method signature after a C++ method declaration, please ensure that **only the variable types, not the variable names**, are retained in the parameters of the Java method signature. For example, the method add(Int a, Int b) must be written as // `add(Int,Int)`
#     5. If you declare a pure virtual class corresponding to a Java interface, please ensure that they have at least one virtual method.
#     {"6. the following header files can be directly included and don't need to be declared:"
#      + ",".join(implemented_additional_file_names) if len(implemented_additional_file_names) > 0 else ""}
# </note>

# <example>
#     here is an output example:
#     <translated>
#         ```cpp
#         #ifndef EXAMPLE_H
#         #define EXAMPLE_H
#         #include <vector>
#         #include <string>
#         #include "MyClass.h"
#         #include "MyInterface.h"

#         class Example: public MyClass, public MyInterface {{
#         protected:
#             int a; // `int a`
#             std::string b; // `String b`

#             void method1(std::string& u, std::string v); // `method1(String,String)`
#             std::vector<std::string>* method2(int i); // `method2(int)`
#         }};
#         #endif // EXAMPLE_H
#         ```
#     </translated>

#     {"""<external-class>
#         ```cpp
#         // MyClass.h
#         #ifndef MYCLASS_H
#         #define MYCLASS_H

#         class MyClass {{
#             // neccessary fields and methods declarations.
#         }};
     
#         #endif // MYCLASS_H
#         ```
#         ```cpp
#         // MyInterface.h
#         #ifndef MYINTERFACE_H
#         #define MYINTERFACE_H
#         class MyInterface {{
#             // neccessary methods declarations.
#         }};
#         #endif // MYINTERFACE_H
#         ```
#     </external-class>""" if len(additional_file_names) > 0 else ""}
# </example>
#     """
#     return prompt