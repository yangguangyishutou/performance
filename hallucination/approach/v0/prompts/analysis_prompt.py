

json_example = """{
    "function_count": 2,
    "analysis":[
        {
            "signature": "signature1",
            "errors": [
                {
                    "error_type": "SYNTAX_LANGUAGE_ERROR",
                    "error_detail": "missing header file: <iostream>"
                },
                {
                    "error_type": "DECLARE_DEFINITION_MISMATCH",
                    "error_detail": "the function call of xxx has mismatched parameter table"
                }
            ]
        },
        {
            "signature": "signature2",
            "errors": [
                ...
            ]
        }
    ]
}
"""

def get_analysis_prompt(json_data: str) -> str:
    return f"""
You need to analyze the compilation results of a series of C++ functions. These functions were directly translated from Java programs and therefore contain many errors. We compiled each function individually and recorded the compilation output. Please analyze the code and compilation process of each method, and identify typical errors for the functions that failed to compile. 
Here is the JSON data of the C++ file:
{json_data}
Now please categorize the errors in each function into the following types:
1. SYNTAX_LANGUAGE_ERROR: Syntax and language feature errors
2. TYPE_SYSTEM_ERROR: Errors of type system, e.g., variable/parameter type mismatch; incorrect return value type; type undefined or incomplete; illegal type conversion, ...
3. DECLARE_DEFINITION_MISMATCH: Inconsistent declaration and definition signatures, or mismatched parameter tables.
4. MISSING_UNDEFINED_SYMBOLS: Missing or undefined functions/variables/classes/...
5. INHERITANCE_VIRTUAL_ERROR: Issues related to override, virtual, and abstract classes, etc.
6. CONSTRUCTOR_DESTRUCTOR_ERROR: Issues related to constructor and destructor.
7. TEMPLATE_ERROR: Template issues related to declaration, instantiation, derivation, etc.
8. ACCESS_SCOPE_ERROR: Access control and scope errors
9. REDEFINITION_ERROR: Redefinition of variables, functions, or classes.
10. BUILD_INCLUDE_ERROR: Errors of wrong building system, missing header files, wrong dependencies, etc.
11. OTHER_ERROR: Other unexpected errors.
The response should be in JSON format like:
{json_example}
"""