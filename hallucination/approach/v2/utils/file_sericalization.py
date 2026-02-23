import json
from pathlib import Path
from Generator import Generator
from prompts.file_sericalizeation_prompt import serialize_file_prompt, serialize_file_output_schema
from path_config import cfg_empirical_project_names, cfg_empirical_output_dir_path, cfg_empirical_graph_dir_path
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
            file_content = file.read_text()
            files.append(file.name)
            prompt = serialize_file_prompt(file_content)
            prompts.append(prompt)
    # print(prompt)
    response = generator.generate(prompts)
    return {file: res for file, res in zip(files, response)}


    
if __name__ == "__main__":
    generator = Generator("qwen-flash")
    for project_name in cfg_empirical_project_names:
        try:
            dir_path = cfg_empirical_output_dir_path("deepseek", project_name, "class")
            files = serialize_file(dir_path, generator)
            graph_dir = cfg_empirical_graph_dir_path("deepseek", project_name, "class")
            for file, res in files.items():
                try:
                    graph_file = graph_dir / file.replace(".cpp", ".json").replace(".h", ".json")
                    json_obj = json.loads(get_json_code(res))
                    graph_file.write_text(json.dumps(json_obj, indent=4))
                    print(f"Serialized {file} to {graph_file}")
                except:
                    print(f"Error serializing {file}")
                    continue
        except:
            print(f"Error serializing {project_name}")
            continue
        
        
    
            
    