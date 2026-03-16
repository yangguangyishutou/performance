from pathlib import Path
import sys

# 本项目根目录
# project_root_dir_path = Path(r"D:\projects\sitp\sitp-dataset")
project_root_dir_path = Path(__file__).resolve().parent.parent.parent
# 要翻译的原始项目目录
source_project_dir_path = project_root_dir_path / "source_projects"
# 输出总目录
output_root_dir_path = project_root_dir_path / "output" / "v1"

def make_dir(func):
    def wrapper(*args, **kwargs):
        dir_path = func(*args, **kwargs)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
        return dir_path
    return wrapper

cfg_parser_tool_path = project_root_dir_path / "approach" / "v1" / "parser_tool"
# 判断是windows还是Linux
is_windows = sys.platform.startswith("win")
if is_windows:
    cfg_gradlew_file_path = project_root_dir_path / "approach" / "v1" / "parser_tool" / "gradlew.bat"
else:
    cfg_gradlew_file_path = project_root_dir_path / "approach" / "v1" / "parser_tool" / "gradlew"

@make_dir
def cfg_split_output_dir_path(ai_name:str, project_name:str) -> Path:
    """本目录存放分割后的原始代码"""
    return output_root_dir_path / project_name / ai_name / "split"

def cfg_method_call_file_path(project_name:str) -> Path:
    """储存方法调用信息的文件"""
    return source_project_dir_path / project_name / "method_call.txt"

def cfg_source_project_path(project_name:str) -> Path:
    """原始项目目录"""
    return source_project_dir_path / project_name


@make_dir
def cfg_translated_project_dir_path(ai_name:str, project_name:str) -> Path:
    """翻译后的项目根目录，存放所有翻译后生成的文件"""
    return output_root_dir_path / project_name / ai_name

@make_dir
def cfg_binary_graph_dir_path(ai_name:str, project_name:str) -> Path:
    """二进制图结构文件的存放目录"""
    return output_root_dir_path / project_name / ai_name / "bin"

def cfg_binary_graph_file_path(ai_name:str, project_name:str) -> Path:
    """二进制图结构文件"""
    return cfg_binary_graph_dir_path(ai_name, project_name) / "nodes.pkl"

@make_dir
def cfg_translate_detail_dir(ai_name:str, project_name:str) -> Path:
    """详细的翻译过程记录"""
    return output_root_dir_path / project_name / ai_name / "detail"

@make_dir
def cfg_translate_result_dir_path(ai_name:str, project_name:str) -> Path:
    """翻译结果目录"""
    return output_root_dir_path / project_name / ai_name / "result"

def cfg_review_dir_path(ai_name:str, project_name:str) -> Path:
    """修改审核目录"""
    return output_root_dir_path / project_name / ai_name / "review"

def cfg_review_prompt_file_path():
    # return project_root_dir_path / "approach" / "prompts" / "review_prompt.md"
    return Path(__file__).parent / "prompts" / "review_prompt.md"

@make_dir
def cfg_eval_dir_path(ai_name:str, project_name:str) -> Path:
    """评估目录"""
    return output_root_dir_path / project_name / ai_name / "eval"

