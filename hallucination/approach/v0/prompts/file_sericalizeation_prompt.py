json_example = """{
    "file_name": "example.cpp",
    "includes": [
        "iostream",
        "string"
    ],
    "variables":[ 
        {
            "name": "variable",
            "variable_code": "const std::string variable = \"variable_value\";"
        }
    ]
    "functions": [ 
        {
            "signature": "Example::function(std::string)",
            "function_code": "void Example::function(std::string str) { std::cout << str << std::endl; }"
        }
        ...
    ]
}
"""

def serialize_file_prompt(file_content: str) -> str:
    """
    Serialize the file content to JSON format.
    """
    prompt = f"""
Please accurately serialize the following C++ code into a valid JSON format:
{file_content}

Your output must strictly follow this JSON structure:
{json_example}

Important requirements:
1. The output must be a valid JSON object with no syntax errors.
2. All code snippets must be exactly as they appear in the original file, preserving whitespace and formatting.
3. Include all 4 mandatory fields:
   - file_name: The exact name of the file, including its extension (e.g., "example.cpp").
   - includes: A list of all include files, including:
     * Standard libraries (e.g., "iostream", "string")
     * User-defined header files (e.g., "example.h", "Math.h")
   - variables: A list of only top-level variables defined in the file(e.g., global variables, global static variables, class static member variables), each variable entry must contain:
     * name: The variable's identifier
     * variable_code: The complete original line(s) of code for the variable declaration or assignment
     * If no top-level variables are present, provide an empty list []
   - functions: A list of all function definitions, where each function entry contains:
     * signature: The function signature in the format "ClassName::function(parameter_types)" (no return type, no parameter names)
     * function_code: The complete original function definition, including the full declaration and body

Please ensure your output is precise, complete, and matches the specified JSON structure exactly.
"""
    return prompt

serialize_file_output_schema = {
    "type": "object",
    "properties": {
        "file_name": {
            "type": "string"
        },
        "includes": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "variables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "variable_code": {
                        "type": "string"
                    }
                }
            }
        },
        "functions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "signature": {
                        "type": "string"
                    },
                    "function_code": {
                        "type": "string"
                    },
                    "success": {
                        "type": "boolean"
                    },
                    "log_output": {
                        "type": "string"
                    },
                    "errors":{
                        "type": "array",
                        "items": {
                            "error_type": {
                                "type": "string"
                            },
                            "error_detail": {
                                "type": "string"
                            }
                        }
                    }
                },
                "required": [
                    "signature",
                    "function_code",
                    "success"
                ]
            }
        }
    },
    "required": [
        "file_name",
        "includes",
        "variables",
        "functions"
    ]
}