"""
头文件翻译生成步骤
负责生成头文件的C++翻译代码
"""
import json
from typing import List
from pathlib import Path
import sys
import re

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph import Header, Method, Project
from utils.Generator import Generator
from utils.str_process import get_cpp_code, get_json_code
from prompts import (
    header_translate_prompt_class, 
    header_translate_prompt_enum,
    header_translate_prompt_interface,
)


class HeaderTranslationStep:
    """头文件翻译生成步骤"""

    def __init__(self, generator: Generator):
        self.generator = generator

    def get_prompt(self, header:Header, all_headers:List[Header]) -> str:
        # enum直接生成翻译提示
        if header.type == "enum":
            prompt = header_translate_prompt_enum(header.source_code)
            header.translate_scheme_prompt = prompt
            return prompt
        
        # class和interface需要有翻译方案才能生成翻译提示
        if not header.translate_scheme:
            raise ValueError(f"header {header.key} has no translate scheme yet")

        all_method_signatures = "\n".join(header.get_all_method_java_signatures())
        available_header_files = "\n".join(Header.get_all_available_header_files(all_headers))
        if header.type == "class":
            prompt = header_translate_prompt_class(header.source_code, header.translate_scheme, all_method_signatures, available_header_files)
            header.translate_prompt = prompt
            return prompt
        elif header.type == "interface":
            prompt = header_translate_prompt_interface(header.source_code, header.translate_scheme, all_method_signatures, available_header_files)
            header.translate_prompt = prompt
            return prompt
        else:
            raise ValueError(f"header_type {header.type} is not supported")

    def process_output(self, header:Header, output:str):
        """
        处理翻译输出
        Args:
            header: 头文件
            output: 翻译输出
        """
        # 处理翻译后代码
        header.raw_translated_code = output
        dict_data = json.loads(get_json_code(output))
        raw_translated_code = dict_data["translated_code"]
        header.translated_code = get_cpp_code(raw_translated_code)

        # 处理方法映射
        if header.type == "enum" or header.type == "interface":
            return
        for mapping in dict_data['method_mapping']:
            if not mapping['original']:
                # TODO 处理新的方法，这里暂时跳过
                continue
            java_signature = mapping['original']
            cpp_declaration = mapping['translated']
            main_function = mapping['main_function']

            method = header.find_method(java_signature)
            if method:
                method.translated_declaration = cpp_declaration
                method.main_function = main_function
            else:
                print(f"warning: unknown method {java_signature} in translated header {header.key}")
                continue
        for method in header.methods:
            if not method.translated_declaration:
                print(f"warning: header {header.key} has no method translated declaration for method {method.key}")

        # 处理额外头文件
        if 'external_header_files' in dict_data:
            for external_header_file in dict_data['external_header_files']:
                file_name, file_content = external_header_file['file_name'], external_header_file['content']
                header.external_header_files[file_name] = file_content


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
            for header in headers:
                self.process_output(header, header.raw_translated_code)
            return

        # 生成翻译提示
        header_prompts = [
            self.get_prompt(header, headers) for header in headers_to_translate
        ]

        # 生成翻译代码
        header_translated_codes = self.generator.generate(header_prompts)

        # 应用翻译结果
        for header, code in zip(headers_to_translate, header_translated_codes):
            self.process_output(header, code)

        print(f"Translated {len(headers_to_translate)} headers.")
