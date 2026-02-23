"""
翻译管道
协调整个翻译过程的各个步骤
"""
from typing import List
from pathlib import Path
import sys

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph import Header, Method, Project
from graph.retrieval_tools import sort_headers
from utils.Generator import Generator

from graph import Header, Method, Project
from steps.step01_graph_build import GraphBuildStep
from steps.step02_header_scheme import HeaderSchemeStep
from steps.step03_header_translation import HeaderTranslationStep
from steps.step04_method_scheme import MethodSchemeStep
from steps.step05_method_translation import MethodTranslationStep
from steps.step06_cpp_file_generation import CppFileGenerationStep
from steps.step07_agent_review import AgentReviewStep
from path_config import cfg_translate_result_dir_path, cfg_graph_dir_path


class TranslationPipeline:
    """翻译管道类，协调整个翻译过程"""

    def __init__(self, generator: Generator):
        self.generator = generator

        # 初始化各个步骤
        self.graph_build_step = GraphBuildStep()
        self.header_scheme_step = HeaderSchemeStep(generator)
        self.header_translation_step = HeaderTranslationStep(generator)
        self.method_scheme_step = MethodSchemeStep(generator)
        self.method_translation_step = MethodTranslationStep(generator)
        self.cpp_file_generation_step = CppFileGenerationStep()
        self.agent_review_step = AgentReviewStep()

    def run_full_translation(self, ai_name: str, project_name:str, 
        force_rebuild_graph: bool = False,
        header_scheme_step:bool = True,
        header_translation_step:bool = True,
        method_scheme_step:bool = True,
        method_translation_step:bool = True,
        cpp_file_generation_step:bool = True,
        agent_review_step:bool = True,
    ) -> None:
        """
        运行完整的翻译流程

        Args:
            ai_name: AI名称
            project_name: 项目名称
            auto_update: 是否自动从文件更新图数据
        """
        try:
            # 1. 构建图
            project = self.graph_build_step.build_graph(ai_name, project_name, force_rebuild_graph)

            # 2. 加载图数据
            headers: List[Header] = project.headers
            method_nodes: List[List[Method]] = project.methods
            
            # 3. 生成头文件翻译方案
            if header_scheme_step:
                self.header_scheme_step.generate_schemes(headers)

            # 4. 生成头文件翻译
            if header_translation_step:
                self.header_translation_step.translate_headers(headers)
            # save_translation_graph(data, ai_name, project_name)
            # return

            Project.save(project, cfg_graph_dir_path(ai_name, project_name))

            # 5. 生成方法翻译方案
            if method_scheme_step:
                self.method_scheme_step.generate_schemes(method_nodes)

            # 6. 生成方法翻译
            if method_translation_step:
                self.method_translation_step.translate_methods(method_nodes)

            # 7. 保存数据
            Project.save(project, cfg_graph_dir_path(ai_name, project_name))

            # 8.生成C++文件
            if cpp_file_generation_step:
                self.cpp_file_generation_step.generate_files(ai_name, project_name, project)

            # 9. 运行智能体修复
            if agent_review_step:
                self.agent_review_step.run_review(ai_name, project_name)

            print("Full translation pipeline completed successfully!")

        except Exception as e:
            print(f"Translation pipeline failed: {str(e)}")
            raise

if __name__ == "__main__":
    from utils.Generator import default_generator
    pipeline = TranslationPipeline(default_generator)
    pipeline.cpp_file_generation_step.generate_files("gpt", "AdviceListenerTestCase")