from pathlib import Path
from typing import Optional, LiteralString
from utils.clean_filename import sanitize_filename  # 导入清洗逻辑
from typing import List, Dict, Any
# from graph.header import Header
import json

class Method:
    def __init__(self, key: str, code: str, source_tag: str, header):
        self.key = key # 类名1$类名2$...$类名n:方法名(参数类型)，项目内唯一
        self.id = id(self) # 唯一标识(注意当从文件加载时， self.id不一定和id(self)相等)
        self.file_name = sanitize_filename(key)
        self.code = code # 源代码
        self.children:set[Method] = set[Method]() # 被我调用的方法
        self.children_external:List[Method] = [] # 被我调用的外部方法
        self.parents:set[Method] = set[Method]() # 调用我的方法
        self.source_tag = source_tag # 如 file1.001
        self.header = header  # 头部信息

        self.is_simple_method = False # 是否是简单方法(样板方法、实现简单且不依赖其他方法的方法)

        # 翻译信息
        self.main_function = "" # 方法的主要功能，规划阶段生成
        self.implementation_detail = "" # 方法的实现详情，翻译阶段生成
        self.temp_header = "" # 临时头

        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translated_declaration = "" # 翻译后的声明

        self.translate_prompt = ""
        self.translated_code = "" # 翻译后的代码

        self.raw_translated_code = ""  # 未经过处理的翻译后的代码

        # 编译信息
        self.compile_unit = ""
        self.compile_output = ""

        # 标注信息
        self.errors = []

        # 迭代信息
        self.history_iter_suggestions:list[list[str]] = [] # 历史迭代建议
        self.iter_suggestion:list[str] = [] # 当前迭代建议

    def get_name(self):
        return self.key.split(':')[1].split('(')[0]

    def __repr__(self):
        return f"Method({self.key})"

    def to_dict(self):
        return {
            "key": self.key, # 唯一标识 
            "id": self.id, # 唯一标识 
            "file_name": self.file_name,
            "code": self.code,
            "children": [child.key for child in self.children], # 被我调用的方法
            "children_external": [child.key for child in self.children_external], # 被我调用的外部方法
            "parents": [parent.key for parent in self.parents], # 调用我的方法
            "source_tag": self.source_tag, # 如 file1.001
            "header": self.header.key,  # 头部信息

            "is_simple_method": self.is_simple_method, # 是否是简单方法(样板方法、实现简单且不依赖其他方法的方法)

            # 翻译信息
            "main_function": self.main_function, # 方法的主要功能，规划阶段生成
            "implementation_detail": self.implementation_detail, # 方法的实现详情，翻译阶段生成
            "temp_header": self.temp_header, # 临时头

            "translate_scheme_prompt": self.translate_scheme_prompt,  # 翻译方案提示
            "translate_scheme": self.translate_scheme,  # 翻译方案

            "translated_declaration": self.translated_declaration, # 翻译后的声明

            "translate_prompt": self.translate_prompt, # 翻译提示
            "translated_code": self.translated_code, # 翻译后的代码

            "raw_translated_code": self.raw_translated_code,  # 未经过处理的翻译后的代码

            # 编译信息
            "compile_unit": self.compile_unit,
            "compile_output": self.compile_output,

            # 标注信息
            "errors": self.errors,

            # 迭代信息
            "history_iter_suggestions": self.history_iter_suggestions, # 历史迭代建议
            "iter_suggestion": self.iter_suggestion, # 当前迭代建议
        }

    def _from_dict(self, data: Dict[str, Any]):
        self.key = data["key"]
        self.id = data["id"] # 唯一标识 
        self.code = data["code"]
        self.source_tag = data["source_tag"]
        self.header = data["header"]
        self.is_simple_method = data["is_simple_method"]
        self.file_name = sanitize_filename(self.key)
        self.code = data["code"]
        self.children = data["children"] # 被我调用的方法
        self.children_external = data["children_external"] # 被我调用的外部方法

        self.parents = data["parents"] # 调用我的方法
        self.source_tag = data["source_tag"] # 如 file1.001

        self.is_simple_method = data["is_simple_method"] # 是否是简单方法(样板方法、实现简单且不依赖其他方法的方法)

        # 翻译信息
        self.main_function = data["main_function"] # 方法的主要功能，规划阶段生成
        self.implementation_detail = data["implementation_detail"] # 方法的实现详情，翻译阶段生成
        self.temp_header = data["temp_header"] # 临时头

        self.translate_scheme_prompt = data["translate_scheme_prompt"]  # 翻译方案提示  
        self.translate_scheme = data["translate_scheme"]  # 翻译方案

        self.translated_declaration = data["translated_declaration"] # 翻译后的声明

        self.translate_prompt = data["translate_prompt"] # 翻译提示
        self.translated_code = data["translated_code"] # 翻译后的代码

        self.raw_translated_code = data["raw_translated_code"]  # 未经过处理的翻译后的代码

        # 编译信息
        self.compile_unit = data["compile_unit"]
        self.compile_output = data["compile_output"]

        # 标注信息
        self.errors = data["errors"]

        # 迭代信息
        # self.history_iter_suggestions = data["history_iter_suggestions"] # 历史迭代建议
        # self.iter_suggestion = data["iter_suggestion"] # 当前迭代建议

    @classmethod
    def _get_from_json(cls, file_path:Path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        method = cls("","","", None)
        method._from_dict(data)
        return method

    
    def __str__(self):
        # 获取 children 和 parents 的 key 值作为字符串
        children_keys = ', '.join([child.key for child in self.children]) if self.children else 'None'
        parents_keys = ', '.join([parent.key for parent in self.parents]) if self.parents else 'None'
    
        # 返回格式化字符串，包含了所需的所有信息
        return (
            f"Key: {self.key}\n"  # 方法的唯一标识
            #f"Code:\n{self.code}\n"  # 方法的源代码
            f"Source Tag: {self.source_tag}\n"  # 源文件标签
            f"Children: {children_keys}\n"  # 被调用的方法
            f"Parents: {parents_keys}\n"  # 调用当前方法的其他方法
            "\n"
        )
    
    def __eq__(self, other):
        return self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def add_iter_suggestion(self, suggestion:str):
        self.iter_suggestion.append(suggestion)

    def clean(self, store_iter_suggestion:bool=False, del_history_iter_suggestion:bool=False):
        self.temp_header = "" # 临时头

        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translated_declaration = "" # 翻译后的声明

        self.translate_prompt = ""
        self.translated_code = "" # 翻译后的代码

        if store_iter_suggestion:
            self.history_iter_suggestions.append(self.iter_suggestion)
        else:
            if del_history_iter_suggestion:
                self.history_iter_suggestions = []
        self.iter_suggestion = []

    def save_to_file(self, file_path:Path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.to_dict(), ensure_ascii=False, indent=4))

    def is_translated(self) -> bool:
        """判断该头文件是否已经翻译完成"""
        # 如果是类/接口，看代码是否生成；如果是枚举，通常直接认为 source_code 存在即可
        # 这里建议以 translated_code 是否有内容为准
        return bool(self.translated_code and self.translated_code.strip())
