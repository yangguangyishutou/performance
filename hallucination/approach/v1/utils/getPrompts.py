from prompts.class_scheme_prompt import class_scheme_prompt
from prompts.enum_translate_prompt import enum_translate_prompt
from prompts.header_translate_prompt import header_translate_prompt
from prompts.method_scheme_prompt import method_scheme_prompt
from prompts.method_translate_prompt import method_translate_prompt

from graph.structure import Header, Method
from typing import List
from kownledge_base.Reference import *


def getHeaderSchemePrompt(h:Header):
    external_classes = {}
    for method in h.methods:
        if method.children_external:
            for clazz, e_method in method.children_external:
                if clazz not in external_classes:
                    external_classes[clazz] = []
                external_classes[clazz].append((method.key, e_method))
    knowledges = get_TH_knowledges(h, external_classes)
    h.translated_scheme_prompt = class_scheme_prompt(h.source_code, knowledges, h.imports)
    return h.translated_scheme_prompt


def getEnumPrompt(h:Header):
    h.translate_prompt = enum_translate_prompt(h.source_code)
    return h.translate_prompt


def getHeaderPrompt(h: Header, all_headers: List[Header]):
    if not h.translate_scheme:
        # 报错信息保留原始 key 方便排查
        raise ValueError(f"header {h.key} has no translate scheme yet")
    
    external_files_need_implement = []
    external_files_implemented = []

    # 获取所有已存在的类名映射（原始 key -> 物理 file_name）
    # 假设 Header 已经有了 file_name 属性
    for external_header_file in h.header_files:
        raw_class_name = external_header_file.split('.')[0]
        
        # 查找对应的 Header 对象
        target_header = next((head for head in all_headers if head.key == raw_class_name), None)
        
        if target_header:
            clean_file_name = f"{target_header.file_name}.h"
            if target_header.is_translated():
                external_files_implemented.append(clean_file_name)
            else:
                external_files_need_implement.append(clean_file_name)
        elif external_header_file in Header.temp_header_codes:
            # 临时头文件通常已经是处理过的文件名
            external_files_implemented.append(external_header_file)
        else:
            # 如果找不到且不是临时文件，则按原始规则处理但需谨慎
            external_files_need_implement.append(external_header_file)

    h.implemented_header_files = external_files_implemented
    # 传递给提示词函数的文件名列表现在全是物理安全的文件名
    h.translate_prompt = header_translate_prompt(h.source_code, h.translate_scheme, external_files_need_implement, external_files_implemented)
    return h.translate_prompt

def getMethodSchemePrompt(n: Method):
    implemented_cpp_methods_declaration_list = []
    if not n.translated_declaration:
        raise ValueError(f"method {n.key} has no translated declaration yet")
    
    for child in n.children:
        implemented_cpp_methods_declaration_list.append(child.translated_declaration)

    knowledges = get_MP_knowledge(n)
    # 将类名改为 file_name，确保 AI 在方案中引用的类名与磁盘上的 .h/.cpp 结构一致
    n.translate_scheme_prompt = method_scheme_prompt(n.code, n.header.file_name, n.translated_declaration, implemented_cpp_methods_declaration_list, knowledges, n.header.translated_fields)
    return n.translate_scheme_prompt

def getMethodPrompt(n: Method):
    if not n.translated_declaration:
        raise ValueError(f"method {n.key} has no translated declaration yet")
    if not n.translate_scheme:
        raise ValueError(f"method {n.key} has no translate scheme yet")
    
    external_methods_implementations = []
    for child in n.children:
        if child.is_translated():
            # 修改注释中的文件名为 file_name
            code_str = f"```cpp\n//{child.header.file_name}.h\n{child.translated_code}\n```"
            external_methods_implementations.append(code_str)
        else:
            print(f"warning: method {n.key} has untranslated child {child.key}")

    # 传递 n.header.file_name，引导 AI 生成符合文件命名的类实现代码
    n.translate_prompt = method_translate_prompt(n.code, n.header.file_name, n.translated_declaration, n.translate_scheme, external_methods_implementations, n.header.translated_fields)
    return n.translate_prompt


# def translate_headers(g:Generator,headers:List[Header], output_dir:Path):
#     for h in headers:
#         h.tempHeader_prompt = getTempHeader(g, h)
#         h.translate_plan_prompt = getClassPlan(g, h)
#         h.translate_prompt = getHeader(g, h, "<plan>", ["<tmpHeader1>", "<tmpHeader2>", "<tmpHeader3>"])
#         h.save_to_dir(output_dir/h.key)

# api_keys = {
#     'gpt':'sk-Wf5pA5Goddqzktb695684491E1B64a15B165383dDf3eF540',
#     'deepseek':'3b144066-c88f-4796-b19e-1fa3cc71253b'
# }
# if __name__ == '__main__':
#     data = retrieve(r"D:\projects\sitp\sitp-dataset\translation_java-cpp","Cookie")
#     g = Generator("deepseek", api_keys['deepseek'])
#     translate_headers(g, data['headers'], Path(r"D:\projects\sitp\sitp-dataset\translation_java-cpp\results\Cookie"))
