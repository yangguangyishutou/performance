"""
方法翻译生成步骤
负责生成方法的C++翻译代码
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
from utils.getPrompts import getMethodPrompt
from utils.answer_process import process_method_translated_code


class MethodTranslationStep:
    """方法翻译生成步骤"""

    def __init__(self, generator: Generator):
        self.generator = generator

    def translate_methods(self, method_nodes: List[List[Method]]) -> None:
        """
        翻译方法（按层级顺序）

        Args:
            method_nodes: 按层级组织的方法节点列表
        """
        print("generate translated methods...")

        total_methods_translated = 0

        # 按层级翻译方法
        for layer_idx, layer in enumerate(method_nodes):
            # 找到当前层级需要翻译的方法
            # nodes_to_translate = [
            #     node for node in layer if not node.translated_code
            # ]
            nodes_to_translate = []
            for node in layer:
                if not node.translated_code:
                    if node.translated_declaration:
                        nodes_to_translate.append(node)
                    else:
                        print(f"warning: method {node.key} has no translated declaration")

            if not nodes_to_translate:
                print(f"Layer {layer_idx}: No methods to translate.")
                continue

            # 生成翻译提示
            method_prompts = [
                getMethodPrompt(node) for node in nodes_to_translate
            ]

            # 生成翻译代码
            method_translated_codes = self.generator.generate(method_prompts)

            # 应用翻译结果
            for node, code in zip(nodes_to_translate, method_translated_codes):
                node.raw_translated_code = code
                process_method_translated_code(node)

            total_methods_translated += len(nodes_to_translate)
            print(f"Layer {layer_idx}: Translated {len(nodes_to_translate)} methods.")

        # 再次处理所有方法确保翻译完整
        self._process_all_method_translations(method_nodes)

        print(f"Total methods translated: {total_methods_translated}")

    def _process_all_method_translations(self, method_nodes: List[List[Method]]) -> None:
        """
        处理所有方法的翻译代码

        Args:
            method_nodes: 按层级组织的方法节点列表
        """
        for layer in method_nodes:
            for node in layer:
                if node.raw_translated_code:
                    process_method_translated_code(node)