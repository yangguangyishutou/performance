import os
import sys
import subprocess
from pathlib import Path    

apprach_dir_path = Path(__file__).parent.parent
if apprach_dir_path not in sys.path:
    sys.path.append(str(apprach_dir_path))

from graph import retrieve_project, Project
from path_config import cfg_split_output_dir_path, cfg_gradlew_file_path, cfg_source_project_path, cfg_parser_tool_path, cfg_graph_dir_path
import shutil

class GraphBuildStep:
    """图构建步骤"""
    def __init__(self):
        pass

    def generate_split(self, ai_name: str, project_name: str) -> None:
        """生成图分割"""
        command = f"cd {cfg_parser_tool_path} && {cfg_gradlew_file_path} run --args=\"{cfg_source_project_path(project_name)} {cfg_split_output_dir_path(ai_name, project_name)}\""
        print(command)
        os.system(command)

    def build_graph(self, ai_name: str, project_name: str, force_rebuild: bool = False) -> Project:
        """构建图"""
        split_dir = cfg_split_output_dir_path(ai_name, project_name)
        if not split_dir.exists() or not list(split_dir.iterdir()) or force_rebuild:
            self.generate_split(ai_name, project_name)
        else:
            print(f"Split files already exist in {split_dir}, skip split.")
        
        graph_dir = cfg_graph_dir_path(ai_name, project_name)
        if not graph_dir.exists() or force_rebuild:
            # 删除重建
            if graph_dir.exists():
                shutil.rmtree(graph_dir)
            data = retrieve_project(ai_name, project_name)
            project = Project(project_name, data["method_nodes"], data["headers"])
            Project.save(project, graph_dir)
            print(f"graph files in {graph_dir} generated.")
        else:
            project = Project.load(graph_dir)
            
        return project

if __name__ == "__main__":
    graph_build_step = GraphBuildStep()
    graph_build_step.build_graph("gpt", "AdviceListenerTestCase")
