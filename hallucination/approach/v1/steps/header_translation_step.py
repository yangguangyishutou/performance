"""
头文件翻译生成步骤
负责生成头文件的C++翻译代码
"""
from typing import List
from pathlib import Path
import sys

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.structure import Header
from utils.Generator import Generator
from utils.getPrompts import getHeaderPrompt, getEnumPrompt
from utils.answer_process import (
    process_header_translated_code,
    get_external_implement_from_translated,
    pre_process_methods
)


class HeaderTranslationStep:
    """头文件翻译生成步骤"""

    def __init__(self, generator: Generator):
        self.generator = generator

    def translate_headers(self, headers: List[Header]) -> None:
        """
        翻译头文件

        Args:
            headers: 头文件列表
        """
        print("generate translated headers...")

        # 找到需要翻译的头文件
        headers_to_translate = [
            h for h in headers if not h.translated_code
        ]

        if not headers_to_translate:
            print("No headers to translate.")
            self._process_all_headers(headers)
            return

        # 生成翻译提示
        header_prompts = []
        for header in headers_to_translate:
            if header.type == "enum":
                header_prompts.append(getEnumPrompt(header))
            else:
                header_prompts.append(getHeaderPrompt(header, headers))

        # 生成翻译代码
        header_translated_codes = self.generator.generate(header_prompts)

        # 应用翻译结果
        for header, code in zip(headers_to_translate, header_translated_codes):
            header.raw_translated_code = code

        # 处理所有头文件的翻译代码
        self._process_all_headers(headers)

        print(f"Translated {len(headers_to_translate)} headers.")

    def _process_all_headers(self, headers: List[Header]) -> None:
        """
        处理所有头文件的翻译代码

        Args:
            headers: 头文件列表
        """
        for header in headers:
            if header.raw_translated_code:
                process_header_translated_code(header)
                get_external_implement_from_translated(header)
                pre_process_methods(header)  # 处理空方法