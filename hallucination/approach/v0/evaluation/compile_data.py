import json
from pathlib import Path
import sys
p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)
import pandas as pd
from path_config import cfg_eval_dir_path, cfg_all_project_names

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

def get_project_statistics(project_name, ai_name, strategy):
    """
    Get the statistics of a project.
    """
    eval_dir = cfg_eval_dir_path(ai_name, project_name, strategy)
    if not eval_dir.exists():
        print(f"{eval_dir} does not exist. Skipping.")
        return None

    error_distribution = {error: 0.0 for error in all_error_types}

    function_count = 0
    for file in eval_dir.iterdir():
        if file.suffix == ".json":
            try:
                file_obj = json.loads(file.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                print(f"Error in file {file}")
                raise
            except json.JSONDecodeError:
                print(f"Error in file {file}")
                raise
            for function_obj in file_obj["functions"]:
                function_count += 1
                if "errors" not in function_obj:
                    continue
                for error in function_obj["errors"]:
                    error_type = error["error_type"]
                    if error_type in error_distribution:
                        error_distribution[error_type] += 1
                    else:
                        print(f"{file} Unknown error type: {error_type}")

    print(f"{project_name},{ai_name},{strategy}", end="")
    for error in all_error_types:
        error_distribution[error] /= function_count
        print(f",{error_distribution[error]:.3f}", end="")
    print()


print(f"project_name,ai_name,strategy,{','.join(all_error_types)}")
for project_name in cfg_all_project_names:
    for ai_name in ["deepseek", "qwen", "gpt"]:
        for strategy in ["class", "method"]:
            get_project_statistics(project_name, ai_name, strategy)


    