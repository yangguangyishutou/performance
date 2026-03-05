from typing import List
import re


def method_scheme_prompt(java_method_code:str, class_name:str, class_skeleton:str, cpp_declaration:str, implemented_methods:str):
    json_example = """```json
{
    "class_name": "ExampleClass",
    "method_name": "exampleMethod",
    "method_function": "calculate the sum of two integers",
    "refactoring":[
        {
            "refactor": "refactor content",
            "description": "detailed description"
        },
        {
            ...
        }
    ],
    "mapping":[
        {
            "original": "java_type_name",
            "translated": "cpp_type_name"
        },
        {
            ...
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

```java
{java_method_code}
```
The above Java method is a member of class {class_name} and is supposed to be translated to C++: {cpp_declaration}

Please provide a detailed translation plan for tha Java method, include the following contents:
1. The basic info of the method, including the class name, method name, and the main function of the method.
2. The necessary refactoring to align differences in language features, such as: use RTTI to replace Java's instanceof operator, implement a utility method that can't be directly mapped, etc..; 
3. Mapping of data type, including those that can be directly mapped and those that require custom implementation; 
4. Other additional explanations (if any).

The following classes and methods may be related to the current method, which may help to the implementation of the current method:
{class_skeleton}

{implemented_methods}

The answer should be in the format of json:
{json_example}

Note:
1. Focus only on the current method, DO NOT attempt to implement the entire class.
2. All of the above require specific solutions to be provided, DO NOT provide ambiguous answers.
    """

method_scheme_output_schema = {
    "type": "object",
    "properties": {
        "class_name": {
            "type": "string"
        },
        "method_name": {
            "type": "string"
        },
        "method_function": {
            "type": "string"
        },
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

# def method_scheme_prompt(java_method_code:str, class_name:str, cpp_declaration:str, implemented_cpp_methods_declaration_list:List[str], related_knowledges:List[str], class_fields:List[str]):
#     if len(implemented_cpp_methods_declaration_list) > 0:
#         implemented_methods = '\n'.join(implemented_cpp_methods_declaration_list)
#     else:
#         implemented_methods = ""

#     suggestions = ""
#     if len(related_knowledges):
#         suggestions = ',\n'.join([(str(i+1) + '.' + related_knowledges[i]) for i in range(len(related_knowledges))])

#     fuzzy_scount = java_method_code.count(";")
#     class_fields_str = '\n'.join(class_fields)
#     prompt = f"""
# <system>
#     You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.
# </system>

# <context>
#     The following is a Java method from class {class_name}
#     ```java
#     {java_method_code}
#     ```
#     Now, it is supposed to be translated to the following C++ method:
#     {cpp_declaration}
# </context>

# <instruction>
#     Provide a detailed translation plan for tha Java method, include the following contents:
#     1. Mapping of data type, including those that can be directly mapped and those that require custom implementation. mark this part with <mapping></mapping> tags; 
#     2. The necessary refactoring to align differences in language features. Mark this part with <refactoring></refactoring> tags; 
#     3. Additional custom classes that will be used in C++ code and need to be declared, use /"None/" if no custom classes are needed. Mark this part with <additional-class></additional-class> tags;
#     4. Additional custom methods that will be used in C++ code and need to be declared(including class methods), use /"None/" if no custom methods are needed. Mark this part with <additional-method></additional-method> tags;
#     5. Other precautions, mark this part with <precaution></precaution> tags; 

#     {"SPECIAL CASE: If this is a very short boilerplate method and does not contain complex dependencies, then omit all the above content and directly provide the translation result, mark this part with <implementation></implementation> tags, except for this case, only provide the solution and do not provide specific code." if fuzzy_scount <= 1 else ""}
# </instruction>

# <note>
#     -. Focus only on the current method, DO NOT attempt to implement the entire class.
#     -. All the above require specific solutions to be provided, DO NOT provide ambiguous answers.
#     {f"- The followings are fields of the class {class_name} for reference:\n {class_fields_str}" if class_fields_str else ""}
#     {"-. The following classes and methods have already been implemented in C++, the header files where these methods are located have the same name as the classes they belong to, they DO NOT NEED to appear in <additional-class> or <addtional-method> tags:\n" + implemented_methods if implemented_methods else ""}
# </note>

# <suggestion>
# {suggestions}
# </suggestion>

# <example>
#     For example, if we have the following Java method form Class Example:
#     ```java
#     public String method1(String a, List<String> l, Processor p){{
#         boolean isSubstring = false;
#         if (l != null) {{
#             for (String str : l) {{
#                 if (str != null && str.contains(a)) {{
#                     isSubstring = true;
#                     break;
#                 }}
#             }}
#         }}
        
#         String joined;
#         if (isSubstring) {{
#             joined = String.join(",", l);
#         }} else {{
#             String[] newArray = Arrays.copyOf(l, l.length + 1);
#             newArray[newArray.length - 1] = a;
#             joined = String.join(",", newArray);
#         }}
        
#         return processor.process(joined);
#     }}
#     ```
#     The following is an example translation plan to translate the above Java method to C++ method `std::string Example::method1(std::string a, const std::vector<std::string>& l, Processor p)`:
#     <mapping>
#         String -> std::string
#         List -> std::vector
#         Processor -> Processor(custom class)
#     </mapping>

#     <refactoring>
#         1. To replace the java method Arrays.copyOf, first create a vector container of the target size, and then copy the original content into it.
#         2. The String.join does not exist in C++, we can use a custom implementation `std::string join(const std::vector<std::string>& vec, const std::string& delimiter)` instead.
#         3. Custom class `Processor` needs to be implemented, and it should contain a `std::string process(const std::string& input)` method.
#     </refactoring>

#     <additional-class>
#         Processor
#     </addtional-class>

#     <additional-method>
#         `std::string join(const std::vector<std::string>& vec, const std::string& delimiter)`
#         `std::string Processor::process(const std::string& input)`
#     </additional-method>

#     <precaution>
#         1. Some non-null checks in this method are not necessary in C++ version.
#     </precaution>    
# </example>

# {"""<example>
#     Another example:
#     ```java
#     public String getName(){{
#         return this.name;
#     }}
#     ```
#     It is a boilerplate getter method, so directly provide the translated C++ method implementation:
#     <implementation>
#     ```cpp
#     #include <string>
#     std::string Example::getName(){{
#         return this->name;
#     }}
#     ```
#     </implementation>
# </example>""" if fuzzy_scount <= 3 else ""}
#     """
#     return prompt