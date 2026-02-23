import json
from pathlib import Path
import sys
p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)
from utils.Generator import Generator
from prompts.file_sericalizeation_prompt import serialize_file_prompt, serialize_file_output_schema
from path_config import cfg_eval_dir_path, cfg_translate_result_dir_path, cfg_review_dir_path, cfg_all_project_names

from typing import List
from utils.str_process import get_json_code



def serialize_file(dir_path: Path, generator: Generator):
    """
    Serialize the file content to JSON format.
    """
    files = []
    prompts = []
    for file in dir_path.iterdir():
        if file.suffix == ".cpp":
            file_content = file.read_text(encoding="utf-8")
            files.append(file.name)
            prompt = serialize_file_prompt(file_content)
            prompts.append(prompt)
    # print(prompt)
    response = generator.generate(prompts)
    return {file: res for file, res in zip(files, response)}


def serialize_review_file(ai_name):
    generator = Generator("qwen-flash")
    for project_name in cfg_all_project_names:
        try:
            dir_path = cfg_review_dir_path(ai_name, project_name)
            files = serialize_file(dir_path, generator)
            eval_dir = cfg_eval_dir_path(ai_name, project_name)
            for file, res in files.items():
                try:
                    eval_file = eval_dir / file.replace(".cpp", ".json").replace(".h", ".json")
                    json_obj = json.loads(get_json_code(res))
                    eval_file.write_text(json.dumps(json_obj, indent=4))
                    print(f"Serialized {file} to {eval_file}")
                except Exception as e:
                    print(f"Error serializing {file}: {e}")
                    continue
        except Exception as e:
            print(f"Error serializing {project_name}: {e}") 
            continue

    
if __name__ == "__main__":
    serialize_review_file("qwen")
        
        
    
            
    