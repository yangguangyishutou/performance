import json
from pathlib import Path
import sys
p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)
from typing import Optional

from path_config import cfg_eval_dir_path
from utils.Generator import Generator
from utils.str_process import get_json_code
from prompts.analysis_prompt import get_analysis_prompt
from prompts.file_sericalizeation_prompt import serialize_file_output_schema
from path_config import cfg_all_project_names

import jsonschema

def find_function(functions: list, signature: str) -> Optional[dict]:
    if not functions:
        return None
    for function in functions:
        if function["signature"] == signature:
            return function
    return None

def has_error(functions: list) -> bool:
    for function in functions:
        if "success" in function and function["success"]:
            continue
        return True
    return False

def find_error(function_analysis: Optional[list], file_namesignature:str) -> Optional[dict]:
    if not function_analysis:
        return None
    for function in function_analysis:
        if function["errors"]:
            return function
    return None

"""
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
"""
all_error_types = [
    "SYNTAX_LANGUAGE_ERROR",
    "TYPE_SYSTEM_ERROR",
    "DECLARE_DEFINITION_MISMATCH",
    "MISSING_UNDEFINED_SYMBOLS",
    "INHERITANCE_VIRTUAL_ERROR",
    "CONSTRUCTOR_DESTRUCTOR_ERROR",
    "TEMPLATE_ERROR",
    "ACCESS_SCOPE_ERROR",
    "REDEFINITION_ERROR",
    "BUILD_INCLUDE_ERROR",
    "OTHER_ERROR",
]

def analyze_error(ai_name, project_name, strategy, generator: Generator):
    """
    分析错误原因
    """
    error_statistics = {error_type: 0 for error_type in all_error_types}

    eval_path = cfg_eval_dir_path(ai_name, project_name, strategy)
    if not eval_path.exists():
        print(f"{project_name}-{ai_name}-{strategy} translated does not exist. Skipping.")
        return error_statistics
    json_datas = {}
    prompts = []
    files_with_error = []
    for file in eval_path.iterdir():
        if file.suffix == ".json":
            try:
                file_obj = json.loads(file.read_text(encoding="utf-8"))
                jsonschema.validate(instance=file_obj, schema=serialize_file_output_schema)
                for function_obj in file_obj["functions"]:
                    if "errors" in function_obj: # 清除旧的错误信息
                        function_obj["errors"] = []
            except Exception as e:
                print(f"Error in file {file.name}: {e}")
                continue
            json_datas[file.name] = file_obj
            funs = file_obj["functions"]
            if has_error(funs):
                prompts.append(get_analysis_prompt(file_obj))
                files_with_error.append(file.name)

    results = generator.generate(prompts)
    
    for file_name, result in zip(files_with_error, results):
        try:
            file_result_obj = json.loads(get_json_code(result))     
            for analysis in file_result_obj["analysis"]:
                for error in analysis["errors"]:
                    if error["error_type"] in error_statistics:
                        error_statistics[error["error_type"]] += 1
                    else:
                        print(f"Unknown error type: {error['error_type']}")
                        error_statistics["OTHER_ERROR"] += 1
        except Exception as e:
            print(f"Error in file {file_name}: {e}")
            continue
        file_obj = json_datas[file_name]

        for function_with_error_obj in file_result_obj["analysis"]:
            function_obj = find_function(file_obj["functions"], function_with_error_obj["signature"])
            if function_obj:
                function_obj["errors"] = function_with_error_obj["errors"]
            else:
                print(f"function {function_with_error_obj['signature']} not found in file {file_name}")
                
    for file_obj in json_datas.values():
        for function_obj in file_obj["functions"]:
            if "errors" not in function_obj:
                function_obj["errors"] = []

    # 保存分析结果
    for file in cfg_eval_dir_path(ai_name, project_name, strategy).iterdir():
        if file.suffix == ".json" and file.name in json_datas:
            file_obj = json_datas[file.name]
            file.write_text(json.dumps(file_obj, ensure_ascii=False, indent=4), encoding="utf-8")

    return error_statistics

if __name__ == "__main__":
    generator = Generator("deepseek")
    # for project_name in cfg_all_project_names:
    #     for strategy in ["method", "class"]:
    #         for ai_name in ["qwen", "deepseek", "gpt"]:
    #             print(f"Analyzing {ai_name} {project_name} {strategy}")
    #             error_statistics = analyze_error(ai_name, project_name, strategy, generator)
    #             print(error_statistics)

    error_statistics = analyze_error("gpt", "EnableJUnit4MigrationSupport", "method", generator)
    print(error_statistics)

    
    

        





            
            


    




    