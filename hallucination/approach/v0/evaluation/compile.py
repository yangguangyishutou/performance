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
from path_config import cfg_all_project_names, cfg_eval_dir_path, cfg_result_dir_path
import json
from tqdm import tqdm
import traceback


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

def calc_file_compile_rate(project_name, ai_name, strategy):
    """
    Calculate the compile success rate for each file in the project.
    """

    compile_success_count = 0
    total_count = 0

    result_dir_path = cfg_result_dir_path(ai_name, project_name, strategy)

    for file in result_dir_path.iterdir():
        if file.suffix == ".cpp":
            total_count += 1
            success, log_output = compile_file(file)
            if success:
                compile_success_count += 1
    success_rate = compile_success_count / total_count if total_count > 0 else 0
    print(f"{project_name}-{ai_name}-{strategy} total_count: {total_count}, compile_success_count: {compile_success_count}, success_rate: {success_rate}")
    return success_rate

def calc_compile_rate(project_name, ai_name, strategy):
    compile_success_count = 0
    total_count = 0
    
    # 首先计算总函数数
    all_functions = []
    h_file_dir = cfg_result_dir_path(ai_name, project_name, strategy)
    if not h_file_dir.exists():
        print(f"{h_file_dir} does not exist. Skipping.")
        return 0
    temp_file = h_file_dir / "temp.cpp"
    
    for json_file in cfg_eval_dir_path(ai_name, project_name, strategy).iterdir():
        if json_file.suffix == ".json":
            try:
                json_data = json.load(open(json_file, "r", encoding="utf-8"))
                all_functions.append((json_file, json_data))
                total_count += len(json_data["functions"])
            except json.JSONDecodeError as e:
                print(f"Error loading {json_file}: JSON {e}")
                raise
    
    # 使用tqdm显示进度条
    processed_count = 0
    with tqdm(total=total_count, desc=f"Compiling {project_name}-{ai_name}-{strategy}", unit="function") as pbar:
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
                try:
                    temp_file.write_text(code, encoding="gbk")
                    success, log_output = compile_file(temp_file)
                except UnicodeEncodeError as e:
                    success = False
                    print(f"{function['signature']} UnicodeEncodeError: {e}")
                    log_output = str(e)
                except Exception as e:
                    success = False
                    print(f"{function['signature']} Exception: {e}")
                    log_output = "Unknown error"
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
    if total_count == 0:
        print(f"{project_name}-{ai_name}-{strategy} has no functions to compile.")
        return 0
    
    compile_rate = compile_success_count / total_count
    print(f"{project_name}-{ai_name}-{strategy} compile rate: {compile_rate}")
    return compile_rate

if __name__ == "__main__":
    # for project_name in cfg_all_project_names:
    #     for ai_name in ["deepseek", "qwen", "gpt"]:
    #         for strategy in ["class", "method"]:
    #             try:
    #                 compile_rate = calc_compile_rate(project_name, ai_name, strategy)
    #             except Exception as e:
    #                 print(f"{project_name}-{ai_name}-{strategy} compile failed")
    #                 traceback.print_exc()

    for project_name in cfg_all_project_names:
        for ai_name in ["deepseek", "qwen", "gpt"]:
            for strategy in ["class", "method"]:
                try:
                    compile_rate = calc_file_compile_rate(project_name, ai_name, strategy)
                except Exception as e:
                    print(f"{project_name}-{ai_name}-{strategy} compile failed")
                    traceback.print_exc()

    # calc_compile_rate("EnableJUnit4MigrationSupport", "gpt", "method")
    # calc_compile_rate("CircuitBreakerExecutor", "deepseek", "class")
    # calc_compile_rate("CircuitBreakerExecutor", "qwen", "method")
    # calc_compile_rate("CircuitBreakerExecutor", "gpt", "method")
    # calc_compile_rate("Cookie", "qwen", "method")
    # calc_compile_rate("RateLimiterExecutor", "deepseek", "class")
    # calc_compile_rate("RateLimiterExecutor", "gpt", "class")
    # calc_compile_rate("RateLimiterExecutor", "deepseek", "method")
    # calc_compile_rate("RateLimiterExecutor", "qwen", "method")
    # calc_compile_rate("RateLimiterExecutor", "gpt", "method")


