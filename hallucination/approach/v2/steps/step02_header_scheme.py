"""
头文件翻译方案生成步骤
负责生成类/接口/枚举的翻译方案
"""
from typing import List
from pathlib import Path
import json
import sys
import re

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph import Header, Method, Project
from prompts import class_and_interface_scheme_prompt
from utils.Generator import Generator
from utils.str_process import get_json_code, get_cpp_code


class HeaderSchemeStep:
    """头文件翻译方案生成步骤"""

    def __init__(self, generator: Generator):
        self.generator = generator

    def get_prompt(self, header:Header, all_headers:List[Header]):
        java_class_info = str(header.get_complete_info())
        all_class_names_dict = [{"name":h.key, "type":h.type} for h in all_headers]
        all_class_names = str(all_class_names_dict)
        prompt = class_and_interface_scheme_prompt(java_class_info, all_class_names)
        header.translate_scheme_prompt = prompt
        return prompt

    def process_output(self, header:Header, output:str):
        """
        将方案保存在头文件节点中，并提取需要的外部类名到header_files中
        """
        header.translate_scheme = output
        output_dict = json.loads(get_json_code(output))
        for external_class in output_dict["external_classes"]:
            header_file_name = external_class["name"] + ".h"
            if header_file_name in header.external_header_files:
                continue
            header.external_header_files[header_file_name] = ""


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
                if header.translate_scheme:
                    self.process_output(header, header.translate_scheme)
            return

        # 生成翻译方案
        header_scheme_prompts = [
            self.get_prompt(h, headers) for h in headers_to_generate_scheme
        ]

        header_schemes = self.generator.generate(header_scheme_prompts)

        # 应用翻译方案
        for header, scheme in zip(headers_to_generate_scheme, header_schemes):
            self.process_output(header, scheme)

        print(f"Generated schemes for {len(headers_to_generate_scheme)} headers.")