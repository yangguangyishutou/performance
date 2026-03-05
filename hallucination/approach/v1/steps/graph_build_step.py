import os
import sys
import subprocess
from pathlib import Path    

apprach_dir_path = Path(__file__).parent.parent
if apprach_dir_path not in sys.path:
    sys.path.append(str(apprach_dir_path))

from graph.retrieval_tools import main as retrieval_project
from path_config import cfg_split_output_dir_path, cfg_gradlew_file_path, cfg_source_project_path, cfg_parser_tool_path, cfg_binary_graph_file_path

class GraphBuildStep:
    """图构建步骤"""
    def __init__(self):
        pass

    def generate_split(self, ai_name: str, project_name: str) -> None:
        """生成图分割"""
        command = f"cd {cfg_parser_tool_path} && {cfg_gradlew_file_path} run --args=\"{cfg_source_project_path(project_name)} {cfg_split_output_dir_path(ai_name, project_name)}\""
        print(command)
        os.system(command)

    def build_graph(self, ai_name: str, project_name: str) -> None:
        """构建图"""
        split_dir = cfg_split_output_dir_path(ai_name, project_name)
        split_files = os.listdir(split_dir)
        if not split_files:
            self.generate_split(ai_name, project_name)
        else:
            print(f"Split files already exist in {split_dir}, skip split.")
        
        binary_graph_file = cfg_binary_graph_file_path(ai_name, project_name)
        if os.path.exists(binary_graph_file):
            print(f"Binary graph file already exist in {binary_graph_file}, skip build.")
        else:
            retrieval_project(ai_name, project_name)
            print(f"Binary graph file {binary_graph_file} generated.")

if __name__ == "__main__":
    graph_build_step = GraphBuildStep()
    graph_build_step.build_graph("gpt", "AdviceListenerTestCase")
