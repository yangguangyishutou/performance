"""
头文件翻译方案生成步骤
负责生成类/接口/枚举的翻译方案
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
from utils.getPrompts import getHeaderSchemePrompt
from utils.answer_process import process_header_scheme


class HeaderSchemeStep:
    """头文件翻译方案生成步骤"""

    def __init__(self, generator: Generator):
        self.generator = generator

    def generate_schemes(self, headers: List[Header]) -> None:
        """
        生成头文件翻译方案

        Args:
            headers: 头文件列表
        """
        print("generate header translate schemes...")

        # 找到需要生成翻译方案的头文件（排除枚举类型）
        headers_to_generate_scheme = [
            h for h in headers
            if not h.translate_scheme and h.type != "enum"
        ]

        if not headers_to_generate_scheme:
            print("No header schemes to generate.")
            for header in headers:
                process_header_scheme(header)
            return

        # 生成翻译方案
        header_scheme_prompts = [
            getHeaderSchemePrompt(h) for h in headers_to_generate_scheme
        ]

        header_schemes = self.generator.generate(header_scheme_prompts)

        # 应用翻译方案
        for header, scheme in zip(headers_to_generate_scheme, header_schemes):
            header.translate_scheme = scheme

        # 从翻译方案中提取需要的外部类名（不含后缀）
        for header in headers:
            process_header_scheme(header)

        print(f"Generated schemes for {len(headers_to_generate_scheme)} headers.")