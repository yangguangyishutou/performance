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

from graph.structure import Header, Method
from utils.Generator import Generator

from graph.data_loader import load_translation_graph, save_translation_graph, apply_header_updates
from steps.header_scheme_step import HeaderSchemeStep
from steps.header_translation_step import HeaderTranslationStep
from steps.method_scheme_step import MethodSchemeStep
from steps.method_translation_step import MethodTranslationStep
from steps.cpp_file_generation_step import CppFileGenerationStep
from steps.graph_build_step import GraphBuildStep
from steps.agent_review_step import AgentReviewStep
from path_config import cfg_translate_result_dir_path


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

    def run_full_translation(self, ai_name: str, project_name:str, auto_update: bool = False) -> None:
        """
        运行完整的翻译流程

        Args:
            ai_name: AI名称
            project_name: 项目名称
            auto_update: 是否自动从文件更新图数据
        """
        try:
            # 1. 构建图
            self.graph_build_step.build_graph(ai_name, project_name)

            # 2. 加载图数据
            data = load_translation_graph(ai_name, project_name, auto_update=auto_update)
            headers: List[Header] = data['headers']
            method_nodes: List[List[Method]] = data['method_nodes']

            # 3. 生成头文件翻译方案
            self.header_scheme_step.generate_schemes(headers)

            # 4. 生成头文件翻译
            self.header_translation_step.translate_headers(headers)
            # save_translation_graph(data, ai_name, project_name)
            # return

            # 5. 生成方法翻译方案
            self.method_scheme_step.generate_schemes(method_nodes)

            # 6. 生成方法翻译
            self.method_translation_step.translate_methods(method_nodes)

            # 7. 保存数据
            save_translation_graph(data, ai_name, project_name)

            # 8.生成C++文件
            self.cpp_file_generation_step.generate_files(ai_name, project_name)

            # 9.清理Header静态成员(这里属于设计缺陷，在翻译下一个项目时需要先清理)
            Header.temp_header_codes = {}

            # 10. 运行智能体修复
            self.agent_review_step.run_review(ai_name, project_name)

            print("Full translation pipeline completed successfully!")

        except Exception as e:
            print(f"Translation pipeline failed: {str(e)}")
            raise

if __name__ == "__main__":
    from utils.Generator import default_generator
    pipeline = TranslationPipeline(default_generator)
    pipeline.cpp_file_generation_step.generate_files("gpt", "AdviceListenerTestCase")