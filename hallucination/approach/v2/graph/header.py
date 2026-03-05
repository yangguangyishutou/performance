from pathlib import Path
from typing import Optional, LiteralString
from utils.clean_filename import sanitize_filename  # 导入清洗逻辑
from typing import List, Dict, Any
from graph.method import Method
import json

class Header:
    def __init__(self, key:str, source_code: str):
        # 结构信息
        self.key = key
        self.file_name = sanitize_filename(key)
        self.type = "" # class, interface, enum
        self.source_code = source_code
        self.methods:list[Method] = []
        self.imports = []
        self.fields:str = ""
        self.parent_class:str = ""
        self.interfaces:list[str]|list[LiteralString] = []
        # self.external_classes:list[str] = []

        # 翻译信息
        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translate_prompt = "" # 翻译提示
        self.translated_code = ""  # 翻译后的代码
        self.translated_fields:list[str] = []  # 翻译后的字段

        self.external_header_files:Dict[str, str] = {} #[file_name: file_content] 包含的其他头文件的文件名列表 (带.h后缀)(在翻译计划中生成file_name, 在正式翻译中生成file_content)

        self.raw_translated_code = ""  # 未经过处理的翻译后的代码

        self.compile_output = ""  # 编译输出
        # 标注信息
        self.errors = []

        # 迭代信息
        self.iter_suggestion = []  # 迭代建议
        self.history_iter_suggestions:list[list[str]] = []  # 迭代建议历史记录

    def to_dict(self):
        return {
            # 结构信息
            "key": self.key,
            "file_name": self.file_name,    
            "type": self.type,
            "source_code": self.source_code,
            "methods": [method.key for method in self.methods],
            "imports": self.imports,
            "fields": self.fields,
            "parent_class": self.parent_class,
            "interfaces": self.interfaces,
            # self.external_classes:list[str] = []

            # 翻译信息
            "translate_scheme_prompt": self.translate_scheme_prompt,  # 翻译方案提示
            "translate_scheme": self.translate_scheme,  # 翻译方案

            "translate_prompt": self.translate_prompt, # 翻译提示
            "translated_code": self.translated_code,  # 翻译后的代码
            "translated_fields": self.translated_fields,  # 翻译后的字段

            "external_header_files": self.external_header_files, #[file_name: file_content] 包含的其他头文件的文件名列表 (带.h后缀)(在翻译计划中生成file_name, 在正式翻译中生成file_content)

            "raw_translated_code": self.raw_translated_code,  # 未经过处理的翻译后的代码

            "compile_output": self.compile_output,  # 编译输出
            # 标注信息
            "errors": self.errors,

            # 迭代信息
            "iter_suggestion": self.iter_suggestion,  # 迭代建议
            "history_iter_suggestions": self.history_iter_suggestions,  # 迭代建议历史记录
        }

    def _from_dict(self, data: Dict[str, Any]):
        # 结构信息
        self.key = data["key"]
        self.file_name = sanitize_filename(self.key)
        self.type = data["type"] # class, interface, enum
        self.source_code = data["source_code"]
        self.methods = data["methods"]
        self.imports = data["imports"]
        self.fields = data["fields"]
        self.parent_class = data["parent_class"]
        self.interfaces = data["interfaces"]
        # self.external_classes:list[str] = []

        # 翻译信息
        self.translate_scheme_prompt = data["translate_scheme_prompt"]  # 翻译方案提示
        self.translate_scheme = data["translate_scheme"]  # 翻译方案

        self.translate_prompt = data["translate_prompt"] # 翻译提示
        self.translated_code = data["translated_code"]  # 翻译后的代码
        self.translated_fields = data["translated_fields"]  # 翻译后的字段

        self.external_header_files = data["external_header_files"]

        self.raw_translated_code = data["raw_translated_code"]  # 未经过处理的翻译后的代码

        self.compile_output = data["compile_output"]  # 编译输出
        # 标注信息
        self.errors = data["errors"]

        # 迭代信息
        self.iter_suggestion = data["iter_suggestion"]  # 迭代建议
        self.history_iter_suggestions = data["history_iter_suggestions"]  # 迭代建议历史记录

    @classmethod
    def _get_from_json(cls, file_path:Path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        header = cls(data["key"], data["source_code"])
        header._from_dict(data)
        return header


    def get_complete_info(self):
        if self.type == "class":
            return {
                "class_name":self.key,
                "imports":self.imports,
                "class_skeleton":self.source_code,
                "method_bodies":[method.code for method in self.methods]
            }
        elif self.type == "interface":
            return {
                "interface_name":self.key,
                "imports":self.imports,
                "source_code":self.source_code,
            }
        elif self.type == "enum":
            return {
                "enum_name":self.key,
                "imports":self.imports,
                "source_code":self.source_code,
            }
        else:
            raise ValueError(f"Unknown header type: {self.type}")

    def get_all_method_java_signatures(self)->List[str]:
        """
        获取所有方法的java签名
        """
        signatures = []
        for method in self.methods:
            signatures.append(method.key.split(':')[1].replace(' ',''))
        return signatures


    def clean(self, store_iter_suggestion:bool=False, del_history_iter_suggestion:bool=False):
        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translate_prompt = "" # 翻译提示
        self.translated_code = ""  # 翻译后的代码
        self.translated_fields = []  # 翻译后的字段

        self.raw_translated_code = ""  # 未经过处理的翻译后的代码

        self.compile_output = ""  # 编译输出
        self.errors = []

        if store_iter_suggestion:
            self.history_iter_suggestions.append(self.iter_suggestion)
        else:
            if del_history_iter_suggestion:
                self.history_iter_suggestions = []
        self.iter_suggestion = []

    def find_method(self, key:str) :
        key = key.replace(' ','').replace('final','')
        for method in self.methods:
            if method.key.split(':')[1].replace(' ','') == key or method.key == key:
                return method
        return None

    def save_to_file(self, file_path:Path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.to_dict(), ensure_ascii=False, indent=4))

    @classmethod
    def get_all_header_name(cls, headers):
        return [header.key for header in headers]

    @classmethod
    def get_all_available_header_files(cls, headers)->List[str]:
        """
        获取所有可用的头文件
        包含原始项目中所有文件对应的头文件和目前为止添加的所有额外头文件
        """
        available_header_files = [f"{h.file_name}.h" for h in headers]
        for header in headers:
            for header_file in header.external_header_files.keys():
                if header_file not in available_header_files:
                    available_header_files.append(header_file)
        return available_header_files
    
    def is_translated(self) -> bool:
        """判断该头文件是否已经翻译完成"""
        # 如果是类/接口，看代码是否生成；如果是枚举，通常直接认为 source_code 存在即可
        # 这里建议以 translated_code 是否有内容为准
        return bool(self.translated_code and self.translated_code.strip())

