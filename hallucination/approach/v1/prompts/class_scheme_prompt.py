from typing import List
import re


def class_scheme_prompt(java_class_skeleton:str, related_knowledges:List[str], imports:List[str]):
    java_code = java_class_skeleton
    imports_ = ['import ' + i + ';' for i in imports]
    imports_str = '\n'.join(imports_)
    suggestion = ""
    if len(related_knowledges):
        suggestion = ',\n'.join([(str(i+1) + '.' + related_knowledges[i]) for i in range(len(related_knowledges))])
    prompt = f"""
<system>
    You are an advanced AI code migration assistant, participating in a project that migrates a Java repository to a C++ repository. According to the instructions, you will focus on only one issue at a time and gradually handle tasks related to code translation, dependency management, and compilation.
</system>

<context>
    Following is a part of a java file. it contians the member variables and  member functions of a class(the function implements are omitted) , now it is supposed to be translated to a C++ header Including declarations of all fields and methods.
```java
{imports_str}
{java_code}
```
</context>

<instruction>
    Carefully read the java code, then specify a detailed translation scheme, including but not limited to the following contents:
    1. External custom classes which will be used in the translated code, and don't have a corresponding C++ equivalent in the standard library. mark this part with <external-class></external-class> tags;
    2. Mapping of data types and classes. The mapped class may be a class in the C++ Standard Library or a custom class that needs to be implemented. Mark this part with <mapping></mapping> tags; 
    3. The necessary refactoring to align differences in language features, mark this part with <refactoring></refactoring> tags; 
    4. Additional precautions, mark this part with <precaution></precaution> tags; 
</instruction>

<note>
    - All the above require specific solutions to be provided, DO NOT provide ambiguous answers.
    - For classes in the Java standard library, try to use corresponding classes in the C++ standard library. If there is no corresponding class, use a custom class instead.
    - For custom Java classes, use custom C++ classes with the same name.
</note>
{
("\n<suggestion>\n" +
suggestion +
"</suggestion>\n") if len(related_knowledges) > 0 else ""
}

<example>
    The following is an format example:
    <external-class>
        Comparator
        Serializable
    </external-class>

    <mapping>
        String -> std::string
        Integer -> int
        ArrayList -> std::vector
        java.util.Comparator -> Comparator
        java.io.Serializable
    </mapping>

    <refactoring>
        1. The parameter of the `compare` method is of type Object, but there is no Object class in C++. Therefore, we first guess the possible situations of the passed parameter, then use a parent class pointer or void pointer instead, and perform logical operations such as type conversion inside the method.
        2. The Class is an interface, but there is no interface in C++, instead, we use a pure vitual base class to implement the interface.
    </refactoring>

    <precaution>
        1. In C++, static members need to be defined and initialized separately outside the class.
    </precaution>
</example>
    """
    return prompt