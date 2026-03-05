import sys
from pathlib import Path

apprach_dir_path = Path(__file__).parent.parent
if apprach_dir_path not in sys.path:
    sys.path.append(str(apprach_dir_path))

import json
import pandas as pd
from path_config import cfg_split_output_dir_path, cfg_all_project_names, cfg_statistics_dir_path
from scripts.generate_table import df_to_latex_basic

def get_project_summary(ai_name: str, project_name: str):
    split_dir = cfg_split_output_dir_path(ai_name, project_name)
    summary = {}
    for file in split_dir.iterdir():
        if file.suffix == ".json":
            with open(file, "r", encoding='utf-8') as f:
                data = json.load(f)
                main_class = data["className"]
                method_count = data["methodCount"]
                summary[main_class] = method_count
    return summary
    
                

if __name__ == "__main__":
    project_method_count = {}
    df = pd.read_csv(cfg_statistics_dir_path() / "v2-qwen-overall.csv")
    for project_name in cfg_all_project_names:
        summary = get_project_summary("gpt", project_name)
        project_method_count[project_name] = sum(summary.values())
        df.loc[df["compile_unit"] == project_name, "method_count"] = project_method_count[project_name]

    print(project_method_count)

    total_method_count = df["method_count"].sum()
    total_success_count = df["success_count"].sum()
    total_file_count = df["file_count"].sum()
    total_cpp_file_count = df["cpp_file_count"].sum()
    total_success_rate = str(total_success_count / total_cpp_file_count * 100) + "%"

    # 为df增加一行
    df = pd.concat([df, pd.DataFrame({
        "compile_unit": ["TOTAL ALL PROJECTS"],
        "method_count": [total_method_count],
        "success_count": [total_success_count],
        "file_count": [total_file_count],
        "cpp_file_count": [total_cpp_file_count],
        "success_rate": [total_success_rate]
    })], ignore_index=True)



    df.to_csv(cfg_statistics_dir_path() / "empirical-overall.csv", index=False)
    
    
    
        
        