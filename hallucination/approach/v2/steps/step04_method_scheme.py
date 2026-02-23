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

from graph import Header, Method, Project
from utils.Generator import Generator
from prompts import method_scheme_prompt
from utils.str_process import get_json_code


class MethodSchemeStep:
    """方法翻译方案生成步骤"""

    def __init__(self, generator: Generator):
        self.generator = generator

    def get_prompt(self, method:Method) -> str:
        java_method_code = method.code
        h = method.header
        class_name = h.key
        class_skeleton = h.source_code
        if not method.translated_declaration:
            raise ValueError(f"no translated declaration for method {method.key}")
        translated_declaration = method.translated_declaration
        implemented_methods = []
        for child in method.children:
            if not child.translated_declaration:
                print(f"warning: no translated code for <{method.key}>'s child method {child.key}")
                continue
            implemented_methods.append(child.translated_declaration)
        implemented_methods = "\n".join(implemented_methods)
        prompt = method_scheme_prompt(java_method_code, class_name, class_skeleton, translated_declaration, implemented_methods)
        method.translate_scheme_prompt = prompt
        return prompt

    def process_output(self, method:Method, output:str):
        method.translate_scheme = output
        
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
            nodes_to_generate_scheme = []
            for node in layer:
                if not node.translate_scheme and not node.is_simple_method:
                    if node.translated_declaration:
                        nodes_to_generate_scheme.append(node)
                    else:
                        print(f"warning: no translated declaration for method {node.key}")

            if not nodes_to_generate_scheme:
                print(f"Layer {layer_idx}: No method schemes to generate.")
                continue

            # 生成翻译方案提示
            method_scheme_prompts = [
                self.get_prompt(node) for node in nodes_to_generate_scheme
            ]

            # 生成翻译方案
            method_schemes = self.generator.generate(method_scheme_prompts)

            # 应用翻译方案
            for node, scheme in zip(nodes_to_generate_scheme, method_schemes):
                node.translate_scheme = scheme

            total_schemes_generated += len(nodes_to_generate_scheme)
            print(f"Layer {layer_idx}: Generated schemes for {len(nodes_to_generate_scheme)} methods.")

        # 处理所有方法的翻译方案
        for layer in method_nodes:
            for node in layer:
                if node.translate_scheme:
                    self.process_output(node, node.translate_scheme)

        print(f"Total method schemes generated: {total_schemes_generated}")
