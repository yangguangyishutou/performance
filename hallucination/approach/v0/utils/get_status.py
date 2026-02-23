import json
from pathlib import Path
import sys
p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from path_config import cfg_result_dir_path, cfg_eval_dir_path, cfg_all_project_names

with open("status.log", "w") as f:
    print("project_name-ai_name\tclass_result\tclass_eval\tmethod_result\tmethod_eval\n")
    f.write("project_name-ai_name\tclass_result\tclass_eval\tmethod_result\tmethod_eval\n")
    for project_name in cfg_all_project_names:
        for ai_name in ["deepseek", "qwen", "gpt"]:
            print(f"{project_name}-{ai_name}", end="\t")
            f.write(f"{project_name}-{ai_name}\t")
            for strategy in ["class", "method"]:
                result_dir_path = cfg_result_dir_path(ai_name, project_name, strategy)
                if not result_dir_path.exists() or not list(result_dir_path.iterdir()):
                    print(0, end="\t")
                    f.write("0\t")
                else:
                    print(1, end="\t")
                    f.write("1\t")
                eval_dir_path = cfg_eval_dir_path(ai_name, project_name, strategy)
                if not eval_dir_path.exists() or not list(eval_dir_path.iterdir()):
                    print(0, end="\t")
                    f.write("0\t")
                else:
                    print(1, end="\t")
                    f.write("1\t")
            print()
            f.write("\n")
