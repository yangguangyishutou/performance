"""
方法翻译生成步骤
负责生成方法的C++翻译代码
"""
import json
from typing import List
from pathlib import Path
import sys

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph import Header, Method, Project
from utils.Generator import Generator
from utils.str_process import get_json_code, get_cpp_code
from prompts import method_translate_prompt, method_translate_prompt_no_scheme


class MethodTranslationStep:
    """方法翻译生成步骤"""

    def __init__(self, generator: Generator):
        self.generator = generator

    def get_prompt(self, method:Method) -> str:
        translated_declaration = method.translated_declaration
        if not translated_declaration:
            raise ValueError(f"no translated declaration for method {method.key}")

        if method.is_simple_method: # 简单方法，直接翻译
            prompt = method_translate_prompt_no_scheme(
                method.code,
                method.header.key,
                translated_declaration
            )
            method.translated_code = prompt
            return prompt

        else: # 翻译复杂方法
            implemented_methods = []
            for child in method.children:
                if not child.translated_code:
                    print(f"warning: no translated code for <{method.key}>'s child method {child.key}")
                    continue
                implemented_methods.append(child.translated_code)
            implemented_methods = "\n".join(implemented_methods)

            prompt = method_translate_prompt(
                method.code, 
                method.header.key, 
                method.header.source_code, 
                translated_declaration,
                method.translate_scheme or "(no scheme)",
                implemented_methods
            )
            method.translate_prompt = prompt
            return prompt

    def process_output(self, method:Method, output:str):
        method.raw_translated_code = output
        output_dict = json.loads(get_json_code(output))
        method.implementation_detail = output_dict['method_detail']
        method.translated_code = get_cpp_code(output_dict['implementation'])

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
                self.get_prompt(node) for node in nodes_to_translate
            ]

            # 生成翻译代码
            method_translated_codes = self.generator.generate(method_prompts)

            # 应用翻译结果
            for node, code in zip(nodes_to_translate, method_translated_codes):
                # node.raw_translated_code = code
                self.process_output(node, code)

            total_methods_translated += len(nodes_to_translate)
            print(f"Layer {layer_idx}: Translated {len(nodes_to_translate)} methods.")

        # 再次处理所有方法确保翻译完整
        for layer in method_nodes:
            for node in layer:
                if node.raw_translated_code:
                    self.process_output(node, node.raw_translated_code)

        print(f"Total methods translated: {total_methods_translated}")