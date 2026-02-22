import re
from pathlib import Path
import sys

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.structure import *

from utils.clean_filename import sanitize_filename  # 导入清洗逻辑

def getCppCode(str):
    pattern = re.compile(r"```cpp\s*([\s\S]*?)\s*```")
    match = pattern.search(str)
    if match:
        return match.group(1)
    else:
        return ""
    
def process_header_scheme(header:Header):
    """
    从翻译方案中提取需要声明的外部类（不含后缀）
    """
    header.header_files = []
    external_classes_parttern = re.compile(r"<external-class>\s*([\s\S]*?)\s*</external-class>")
    external_classes_match = external_classes_parttern.search(header.translate_scheme)
    if not external_classes_match:
        return
    external_classes = external_classes_match.group(1)
    for line in external_classes.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.lower() == "none":
            continue
        file_name = sanitize_filename(line) + '.h'
        if file_name not in header.header_files:
            header.header_files.append(file_name)


def process_header_translated_code(header:Header):
    """
    1. 从原始翻译后头文件中提取C++代码部分
    2. 提取各方法的翻译后声明

    注：纯虚方法不会被提取
    """
    if header.type == 'enum':
        header.translated_code = header.raw_translated_code
        return

    translated_pattern = re.compile(r"<translated>\s*([\s\S]*?)\s*</translated>")
    translated_match = translated_pattern.search(header.raw_translated_code)
    if not translated_match:
        print(f"warning: can not find translated code in {header.key}")
        return

    header.translated_code = getCppCode(translated_match.group(1))
    if header.type != "class":
        print(f"{header.key} is not a class, skip")
        return
    code = header.translated_code
    header.translated_fields = []
    tag_pattern = re.compile(r'//\s*`(.*?)`')
    signatrue_pattern = re.compile(r'(\S+\(.*?\))') # 例：public void myMethod(int int) -> myMethod(int int)
    for line in code.split("\n"):
        tag_match = tag_pattern.search(line)
        # 排除不满足 //`...`的行
        if not tag_match:
            continue
        method_declaration = tag_match.group(1)
        # 排除成员变量的标记行，留下成员函数的标记行
        if not '(' in method_declaration or '=' in method_declaration:
            transalted_field = line.split('//')[0].strip()
            header.translated_fields.append(transalted_field)
            continue
        method_key_match = signatrue_pattern.search(method_declaration)
        # 如果无法从成员函数的标记行中提取到方法签名，属于异常情况
        if not method_key_match:
            print(f'warning: cannot extract method signature from {method_declaration}')
            continue
        method_key = method_key_match.group(1)
        method = header.find_method(method_key)
        # 无法从头文件节点中找到匹配的方法，属于异常情况
        if not method:
            print(f"warning: cannot find method {method_key} in header node {header.key}")
            continue
        translated_declaration = line.split('//')[0].strip()
        if not line.startswith("friend"):
            translated_decl_with_namespace = translated_declaration.replace(method.get_name(), f"{header.key}::{method.get_name()}")
            method.translated_declaration = translated_decl_with_namespace
        else:
            method.translated_declaration = translated_declaration

def get_external_implement_from_translated(header:Header):
    """
    从翻译后的头文件中提取外部实现
    """
    external_classes_pattern = re.compile(r"<external-class>\s*([\s\S]*?)\s*</external-class>")
    external_classes_match = external_classes_pattern.search(header.raw_translated_code)
    if not external_classes_match:
        print(f"class {header.key} has no external implementation")
        return
    cpp_pattern = re.compile(r"```cpp\s*([\s\S]*?)\s*```")
    cpp_blocks_match = cpp_pattern.findall(external_classes_match.group(1))
    for block in cpp_blocks_match:
        first_line = block.split("\n")[0]
        if not first_line.startswith("//"):
            print(f"warning: in {header.key}: external implementation block should start with //")
            continue
        raw_name = first_line.split("//")[1].strip()
        external_file_name = sanitize_filename(raw_name)
        if not external_file_name.endswith(".h"):
            external_file_name += ".h"
        Header.temp_header_codes[external_file_name] = block


def pre_process_methods(header:Header):
    method_body_pattern = re.compile(r"\)[\s\S]*{([\s\S]*)}") # 贪婪匹配
    for method in header.methods:
        body_match = method_body_pattern.search(method.code)
        if not body_match:
            print(f"warning: cannot find method body in {method.key}")
            continue
        if body_match.group(1).strip():
            continue
        print(f"{header.key}:{method.key} is a empty method.")
        name = method.key.split('(')[0]
        declaration = method.translated_declaration.replace(name, f"{header.key}::{name}").replace(';','')
        method.translated_code = f"{declaration} {{}}"
        method.translate_scheme = "// ignore this line"

def process_method_translate_scheme(method:Method):
    """
    从翻译方案原始回答中处理翻译方案：
        如果方案中仅有<implementation>标记，则直接提取翻译后代码
    """
    implementation_pattern = re.compile(r"<implementation>\s*([\s\S]*?)\s*</implementation>")
    other_keywords = [
        "<mapping>",
        "<refactoring>",
        "<additional-class>",
        "<additional-method>",
        "<precaution>"
    ]
    for kw in other_keywords:
        if kw not in method.translate_scheme:
            implementation_match = implementation_pattern.search(method.translate_scheme)
            if implementation_match:
                method.is_boilerplate = True
                method.translated_code = getCppCode(implementation_match.group(1))
                if not method.translated_code:
                    print(f"warning: cannot find implementation code in {method.key}")
            return
    

def process_method_translated_code(method:Method):
    """
    从方法翻译原始回答中提取有效内容
    1. 翻译后代码
    2. 依赖头文件代码
    """

    implementation_pattern = re.compile(r"<implementation>\s*([\s\S]*?)\s*</implementation>")
    implementation_match = implementation_pattern.search(method.raw_translated_code)
    if not implementation_match:
        print(f"warning: can not find implementation code in {method.key}")
        return
    method.translated_code = ""
    code = getCppCode(implementation_match.group(1))
    for line in code.split("\n"):
        if line.strip() == "#include \"temp_header.h\"":
            continue
        method.translated_code += line + "\n"


    dependency_pattern = re.compile(r"<dependency>\s*([\s\S]*?)\s*</dependency>")
    dependency_match = dependency_pattern.search(method.raw_translated_code)
    if dependency_match:
        method.temp_header = getCppCode(dependency_match.group(1))
    else:
        method.temp_header = ""