from typing import List
import re


def class_and_interface_scheme_prompt(java_class_info:str, all_class_names:str):
    """
    java_class_info: java类的信息，包含类名、导入的类、类骨架、方法体等，json格式
    all_class_names: 项目中所有对象列表，包括名称和类型（类、接口、枚举）
    """
    json_example = """```json
{
    "refactoring":[
        {
            "refactor": "refactor content",
            "description": "detailed description"
        },
        {
            ...
        }
    ],
    "external_classes": [ // If there is none, leave it blank. The name cannot contain characters other than uppercase and lowercase letters and numbers.
        {
            "name": "ExternalClass1",
            "type": "class"
        },
        {
            "name": "ExternalClass2",
            "type": "enum class"
        }
        {
            "name": "ExternalClass3",
            "type": "pure virtual class"
        }
    ],
    "mapping":[
        {
            "original": "java_class_name1",
            "translated": "cpp_class_name1"
        },
        {
            "original": "java_class_name2",
            "translated": "cpp_class_name2"
        }
    ],
    "additional_explanations": [ // If there is none, leave it blank.
        "additional_explanation1",
        "additional_explanation2"
    ]
}
```
(The comments in the above json content are for explanation only. When actually outputting, please strictly abide by the json syntax and do not add comments.)
    """

    return f"""
You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.

Following is a java file information from the project, now it is supposed to be translated to a C++ header Including declarations of all fields and methods.
{java_class_info}

Carefully read the java code, then specify a detailed translation schema, including the following contents:
1. The necessary refactoring to align differences in language features, such as: use a pure virtual base class to replace an interface, use RTTI to replace Java's instanceof operator, add extra fields and methods to imitate reflection, etc..;
2. Any external C++ classes(include enum class, virtual class, etc.) not in the current project and not in standard library need to be implemented in the future;
3. Mapping of data types and classes. The mapped class may be a primitive C++ type, composite type, a class in the C++ Standard Library or a custom class that needs to be implemented;
4. Other additional explanations (if any).

The available headers in the current project are as follows. If you need to use a header that is not included in them, please add it to the list of external classes.
{all_class_names}

The answer should be in the format of json:
{json_example}

Notes:
1. All the above require specific solutions to be provided, DO NOT provide ambiguous answers, and DO NOT directly provide C++ code.
2. For classes in the Java standard library, try to use corresponding classes in the C++ standard library. If there is no corresponding class, add a external class instead.
    """

header_scheme_output_schema = {
    "type": "object",
    "properties": {
        "refactoring": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "refactor": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    }
                }
            }
        },
        "external_classes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "type": {
                        "type": "string"
                    }
                }
            }
        },
        "mapping": {
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
        "additional_explanations": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    }
}




# def class_scheme_prompt(java_class_skeleton:str, related_knowledges:List[str], imports:List[str]):
#     java_code = java_class_skeleton
#     imports_ = ['import ' + i + ';' for i in imports]
#     imports_str = '\n'.join(imports_)
#     suggestion = ""
#     if len(related_knowledges):
#         suggestion = ',\n'.join([(str(i+1) + '.' + related_knowledges[i]) for i in range(len(related_knowledges))])
#     prompt = f"""
# <system>
#     You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.
# </system>

# <context>
#     Following is a part of a java file. it contians the member variables and  member functions of a class(the function implements are omitted) , now it is supposed to be translated to a C++ header Including declarations of all fields and methods.
# ```java
# {imports_str}
# {java_code}
# ```
# </context>

# <instruction>
#     Carefully read the java code, then specify a detailed translation scheme, including but not limited to the following contents:
#     1. External custom classes which will be used in the translated code, and don't have a corresponding C++ equivalent in the standard library. mark this part with <external-class></external-class> tags;
#     2. Mapping of data types and classes. The mapped class may be a class in the C++ Standard Library or a custom class that needs to be implemented. Mark this part with <mapping></mapping> tags; 
#     3. The necessary refactoring to align differences in language features, mark this part with <refactoring></refactoring> tags; 
#     4. Additional precautions, mark this part with <precaution></precaution> tags; 
# </instruction>

# <note>
#     - All the above require specific solutions to be provided, DO NOT provide ambiguous answers.
#     - For classes in the Java standard library, try to use corresponding classes in the C++ standard library. If there is no corresponding class, use a custom class instead.
#     - For custom Java classes, use custom C++ classes with the same name.
# </note>
# {
# ("\n<suggestion>\n" +
# suggestion +
# "</suggestion>\n") if len(related_knowledges) > 0 else ""
# }

# <example>
#     The following is an format example:
#     <external-class>
#         Comparator
#         Serializable
#     </external-class>

#     <mapping>
#         String -> std::string
#         Integer -> int
#         ArrayList -> std::vector
#         java.util.Comparator -> Comparator
#         java.io.Serializable
#     </mapping>

#     <refactoring>
#         1. The parameter of the `compare` method is of type Object, but there is no Object class in C++. Therefore, we first guess the possible situations of the passed parameter, then use a parent class pointer or void pointer instead, and perform logical operations such as type conversion inside the method.
#         2. The Class is an interface, but there is no interface in C++, instead, we use a pure vitual base class to implement the interface.
#     </refactoring>

#     <precaution>
#         1. In C++, static members need to be defined and initialized separately outside the class.
#     </precaution>
# </example>
#     """
#     return prompt