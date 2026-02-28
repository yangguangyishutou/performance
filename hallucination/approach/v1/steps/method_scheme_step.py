"""
方法翻译方案生成步骤
负责生成方法的翻译方案
"""
from typing import List
from pathlib import Path
import sys

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.structure import Method
from utils.Generator import Generator
from utils.getPrompts import getMethodSchemePrompt
from utils.answer_process import process_method_translate_scheme


class MethodSchemeStep:
    """方法翻译方案生成步骤"""

    def __init__(self, generator: Generator):
        self.generator = generator

    def generate_schemes(self, method_nodes: List[List[Method]]) -> None:
        """
        生成方法翻译方案（按层级顺序）

        Args:
            method_nodes: 按层级组织的方法节点列表
        """
        print("generate method translate schemes...")

        total_schemes_generated = 0

        # 按层级生成翻译方案
        for layer_idx, layer in enumerate(method_nodes):
            # 找到当前层级需要生成翻译方案的方法
            # nodes_to_generate_scheme = [
            #     node for node in layer if not node.translate_scheme and node
            # ]
            nodes_to_generate_scheme = []
            for node in layer:
                if not node.translate_scheme:
                    if node.translated_declaration:
                        nodes_to_generate_scheme.append(node)
                    else:
                        print(f"warning: no translated declaration for method {node.key}")

            if not nodes_to_generate_scheme:
                print(f"Layer {layer_idx}: No method schemes to generate.")
                continue

            # 生成翻译方案提示
            method_scheme_prompts = [
                getMethodSchemePrompt(node) for node in nodes_to_generate_scheme
            ]

            # 生成翻译方案
            method_schemes = self.generator.generate(method_scheme_prompts)

            # 应用翻译方案
            for node, scheme in zip(nodes_to_generate_scheme, method_schemes):
                node.translate_scheme = scheme

            total_schemes_generated += len(nodes_to_generate_scheme)
            print(f"Layer {layer_idx}: Generated schemes for {len(nodes_to_generate_scheme)} methods.")

        # 处理所有方法的翻译方案
        self._process_all_method_schemes(method_nodes)

        print(f"Total method schemes generated: {total_schemes_generated}")

    def _process_all_method_schemes(self, method_nodes: List[List[Method]]) -> None:
        """
        处理所有方法的翻译方案

        Args:
            method_nodes: 按层级组织的方法节点列表
        """
        for layer in method_nodes:
            for node in layer:
                if node.translate_scheme:
                    process_method_translate_scheme(node)