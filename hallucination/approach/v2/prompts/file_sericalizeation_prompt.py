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
Please serialize the following C++ code into JSON format:
{file_content}
Your output should like the following:
{json_example}
The file_name, includes, variables, and functions are required fields, if there is no variable or function in the file, leave the corresponding field empty.
Please strictly adhere to the JSON format for output and avoid outputting extra characters.
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
                    }
                }
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