"""
C++文件生成步骤
负责生成最终的.h和.cpp文件
"""
import os
from pathlib import Path
from typing import List, Dict, Any
import sys

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.structure import Header
from graph.data_loader import load_translation_graph
from path_config import cfg_translate_result_dir_path


class CppFileGenerationStep:
    """C++文件生成步骤"""

    def generate_files(self, ai_name:str, project_name:str, data:Dict|None=None) -> None:
        """
        生成C++头文件和实现文件

        Args:
            output_dir: 输出目录路径
        """
        print("Generating C++ files...")

        # 加载数据
        if data is None:
            data = load_translation_graph(ai_name, project_name)
        headers: List[Header] = data['headers']

        output_dir = cfg_translate_result_dir_path(ai_name, project_name)
        temp_dir = output_dir

        # 生成每个类的.h和.cpp文件
        for header in headers:
            self._generate_header_file(header, str(output_dir))
            self._generate_cpp_file(header, str(output_dir))

        # 生成临时头文件
        self._generate_temp_files(str(temp_dir))

        print(f"Generated C++ files for {len(headers)} classes.")

    def _generate_header_file(self, header: Header, output_dir: str) -> None:
        """
        生成单个头文件

        Args:
            header: 头文件对象
            output_dir: 输出目录路径
        """
        header_path = Path(output_dir) / (header.file_name + '.h')
        # header_includes = [
        #     f'#include "{file_name}"' for file_name in header.header_files
        # ]
        header_includes = []

        header_code = ""
        for line in header.translated_code.split('\n'):
            if line.startswith('#include'):
                if line.strip() not in header_includes:
                    header_includes.append(line.strip())
            else:
                header_code += line + '\n'

        with open(header_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header_includes))
            f.write('\n\n')
            f.write(header_code)

    def _generate_cpp_file(self, header: Header, output_dir: str) -> None:
        """
        生成单个实现文件

        Args:
            header: 头文件对象
            output_dir: 输出目录路径
        """
        cpp_path = Path(output_dir) / (header.file_name + '.cpp')
        cpp_includes = []
        cpp_code = ""

        for method in header.methods:
            if method.translated_code == "":
                print(f"warning: {method.file_name} has no translated code")
                continue

            for line in method.translated_code.split('\n'):
                if line.startswith('#include'):
                    if line.strip() not in cpp_includes:
                        cpp_includes.append(line.strip())
                else:
                    cpp_code += line + '\n'
        if cpp_code.strip() == "":
            print(f"warning: {header.file_name} has no translated code")
            return
        with open(cpp_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cpp_includes))
            f.write('\n\n')
            f.write(cpp_code)

    def _generate_temp_files(self, temp_dir: str) -> None:
        """
        生成临时头文件

        Args:
            temp_dir: 临时目录路径
        """
        for temp_file, file_content in Header.temp_header_codes.items():
            file_path = os.path.join(temp_dir, temp_file)
            if os.path.exists(file_path):
                print(f"warning, temp file {temp_file} conflict with existing file, keep existing file.")
                continue
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)

        print(f"Generated {len(Header.temp_header_codes)} temporary files.")