from pathlib import Path
import sys

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from graph.method import Method
from graph.header import Header
from typing import List, Dict, Optional, LiteralString
from utils.clean_filename import sanitize_filename

from graph.retrieval_tools import *
import json
import shutil


class Project:
    def __init__(self, name: str, methods: List[List[Method]], headers: List[Header]):
        self.name = name
        self.methods = methods
        self.headers = headers

    def find_header(self, key:str) -> Optional[Header]:
        for header in self.headers:
            if header.key == key:
                return header
        return None

    @classmethod
    def save(cls, project, dir_path: Path):
        """
        保存项目到指定目录
        """
        for header in project.headers:
            header_dir = dir_path / header.key
            header_dir.mkdir(parents=True, exist_ok=True)

            header.save_to_file(header_dir / f"{header.key}.json")
            for method in header.methods:
                save_path = header_dir / (method.get_name() + str(method.id) + ".json")
                method.save_to_file(save_path)

    @classmethod
    def load(cls, dir_path: Path):
        """
        从指定目录加载项目
        """
        # self.name = dir_path.name
        # self.headers = []
        project = cls(dir_path.name, [], [])
        all_methods = {}
        for header_dir in dir_path.iterdir():
            if not header_dir.is_dir():
                continue
            for file in header_dir.iterdir():
                if file.name == header_dir.name + ".json":
                    header = Header._get_from_json(file)
                    project.headers.append(header)
                    continue

                method = Method._get_from_json(file)
                all_methods[method.key] = method
            
        for header in project.headers:
            methods_str_list = header.methods
            header.methods = [all_methods[key] for key in methods_str_list]

        for _, method in all_methods.items():
            method.header = project.find_header(method.header)
            if method.header is None:
                raise ValueError(f"Can not find header {method.header} for method {method.key}")
            children_str_list = method.children
            method.children = set([all_methods[key] for key in children_str_list])
            parent_str_list = method.parents
            method.parents = set([all_methods[key] for key in parent_str_list])

            children_external_str_list = method.children_external
            method.children_external = [Method(key, "", "", Header(key.split(':')[0], "")) for key in children_external_str_list]

        project.methods = get_ordered_method_groups(all_methods)
        return project

    @classmethod
    def load_from_source(cls, ai_name:str, project_name:str):
        """
        从数据源加载项目
        """
        data = retrieve_project(ai_name, project_name)
        return cls(project_name, data["method_nodes"], data["headers"])


if __name__ == "__main__":
    from retrieval_tools import *
    data = retrieve_project('deepseek', 'Cookie')
    project = Project('Cookie', data["method_nodes"], data["headers"])

    Project.save(project, Path("test/Cookie"))


            
            

                



