from pathlib import Path
import sys
p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

import subprocess
from typing import List, Dict, Optional
from path_config import cfg_all_project_names, cfg_eval_dir_path, cfg_review_dir_path
import json
from tqdm import tqdm


def compile_file(file_path:Path) -> tuple:
    """
    Compile a single C++ file with -c flag (no linking).
    """
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Derive object file name
        obj_file = file_path.with_suffix(".o")

        # Run clang++ -c
        result = subprocess.run(
            ["clang++", "-c", str(file_path), "-o", str(obj_file)],
            capture_output=True,
            text=True
        )

        success = result.returncode == 0
        log_output = result.stdout + result.stderr
        return success, log_output

    except Exception as e:
        return False, str(e)

def calc_compile_rate(project_name, ai_name):
    compile_success_count = 0
    total_count = 0
    
    # 首先计算总函数数
    all_functions = []
    h_file_dir = cfg_review_dir_path(ai_name, project_name)
    temp_file = h_file_dir / "temp.cpp"
    
    for json_file in cfg_eval_dir_path(ai_name, project_name).iterdir():
        if json_file.suffix == ".json":
            json_data = json.load(open(json_file, "r", encoding="utf-8"))
            all_functions.append((json_file, json_data))
            total_count += len(json_data["functions"])
    
    # 使用tqdm显示进度条
    processed_count = 0
    with tqdm(total=total_count, desc=f"Compiling {project_name}", unit="function") as pbar:
        for json_file, json_data in all_functions:
            variables = json_data["variables"]
            variable_code = "\n".join([variable["variable_code"] for variable in variables])

            includes = []
            for include_file in json_data["includes"]:
                if include_file.endswith(".h"):
                    includes.append(f"#include \"{include_file}\"")
                else:
                    includes.append(f"#include <{include_file}>")
            include_code = "\n".join(includes) + "\n"

            for function in json_data["functions"]:
                code = include_code + variable_code + function["function_code"]
                temp_file.write_text(code)
                success, log_output = compile_file(temp_file)
                if success:
                    compile_success_count += 1
                    function["success"] = True
                    function["log_output"] = log_output
                else:
                    function["success"] = False
                    function["log_output"] = log_output
                
                # 更新进度条
                pbar.update(1)
                processed_count += 1

            json.dump(json_data, open(json_file, "w", encoding="utf-8"), indent=4)

    # 清除临时文件
    if temp_file.exists():
        temp_file.unlink()
    if temp_file.with_suffix(".o").exists():
        temp_file.with_suffix(".o").unlink()

    # 计算编译率
    compile_rate = compile_success_count / total_count
    print(f"{project_name}-{ai_name} compile rate: {compile_rate}")
    
    return compile_rate

if __name__ == "__main__":
    for project_name in cfg_all_project_names:
        calc_compile_rate(project_name, "qwen")


