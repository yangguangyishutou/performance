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
from prompts.file_sericalizeation_prompt import serialize_file_prompt
from path_config import cfg_eval_dir_path, cfg_result_dir_path, cfg_all_project_names

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
    if not prompts:
        return {}
    response = generator.generate(prompts)
    return {file: res for file, res in zip(files, response)}

def serialize_single_file(generator: Generator, ai_name, project_name, strategy, file_name):
    """
    Serialize the file content to JSON format.
    """
    file_path = cfg_result_dir_path(ai_name, project_name, strategy) / file_name
    file_content = file_path.read_text(encoding="utf-8")
    prompt = serialize_file_prompt(file_content)
    response = generator.generate([prompt])
    eval_file = cfg_eval_dir_path(ai_name, project_name, strategy) / file_name.replace(".cpp", ".json").replace(".h", ".json")
    eval_file.write_text(get_json_code(response[0]))
    print(f"Serialized {file_name} to {eval_file}")
    return eval_file

def serialize_project(project_name, ai_name, strategy):
    generator = Generator("deepseek")
    print(f"Serializing {ai_name} {project_name} {strategy}")
    try:
        dir_path = cfg_result_dir_path(ai_name, project_name, strategy)
        files = serialize_file(dir_path, generator)
        eval_dir = cfg_eval_dir_path(ai_name, project_name, strategy)
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


def serialize_result_files(ai_name, strategy):

    """
    Serialize the result files to JSON format.
    """
    generator = Generator("deepseek")
    for project_name in cfg_all_project_names:
        print(f"Serializing {ai_name} {project_name} {strategy}")
        try:
            dir_path = cfg_result_dir_path(ai_name, project_name, strategy)
            files = serialize_file(dir_path, generator)
            eval_dir = cfg_eval_dir_path(ai_name, project_name, strategy)
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
    # for ai_name in ["deepseek", "qwen", "gpt"]:
    #     for strategy in ["class"]:
    #         print(f"Serializing {ai_name} {strategy}")
    #         serialize_result_files(ai_name, strategy)

    # serialize_project("deepseek", "EnableJUnit4MigrationSupport", "method")

    serialize_project("EnableJUnit4MigrationSupport", "qwen", "method")
    serialize_project("CircuitBreakerExecutor", "deepseek", "class")
    serialize_project("CircuitBreakerExecutor", "qwen", "method")
    serialize_project("CircuitBreakerExecutor", "gpt", "method")
    serialize_project("Cookie", "qwen", "method")
    serialize_project("RateLimiterExecutor", "deepseek", "class")
    serialize_project("RateLimiterExecutor", "gpt", "class")
    serialize_project("RateLimiterExecutor", "deepseek", "method")
    serialize_project("RateLimiterExecutor", "qwen", "method")
    serialize_project("RateLimiterExecutor", "gpt", "method")

    # generator = Generator("deepseek")
    # serialize_single_file(generator, 'deepseek', 'EnableJUnit4MigrationSupport', 'method', 'ReflectionSupport.cpp')
    # serialize_single_file(generator, 'deepseek', 'EnableJUnit4MigrationSupport', 'method', 'ReflectionUtils.cpp')
    # serialize_single_file(generator, 'deepseek', 'EnableJUnit4MigrationSupport', 'method', 'Try.cpp')
    # serialize_single_file(generator, 'gpt', 'EnableJUnit4MigrationSupport', 'method', 'ReflectionSupport.cpp')
    # serialize_single_file(generator, 'gpt', 'EnableJUnit4MigrationSupport', 'method', 'ReflectionUtils.cpp')
    # serialize_single_file(generator, 'deepseek', 'IntMath', 'method', 'Converter.cpp')
    # serialize_single_file(generator, 'deepseek', 'IntMath', 'method', 'IntMath.cpp')
    # serialize_single_file(generator, 'deepseek', 'IntMath', 'method', 'Ints.cpp')
    # serialize_single_file(generator, 'deepseek', 'IntMath', 'method', 'Preconditions.cpp')
    # serialize_single_file(generator, 'gpt', 'IntMath', 'method', 'Converter.cpp')
    # serialize_single_file(generator, 'gpt', 'IntMath', 'method', 'IntMath.cpp')
    # serialize_single_file(generator, 'gpt', 'IntMath', 'method', 'Ints.cpp')
    # serialize_single_file(generator, 'gpt', 'IntMath', 'method', 'Preconditions.cpp')


    
        
        
    
            
    